"""Train linear type-prediction heads on frozen sentence-transformer embeddings.

The base encoder (all-MiniLM-L6-v2, 22M params) is frozen.
Only two nn.Linear(384, 79) heads are trained — one predicts the
source entity type, the other predicts the target entity type.

Pipeline:
    1. Load training data and entity types from graph
    2. Encode all queries with the frozen encoder  (~30s on CPU)
    3. Train two linear heads with cross-entropy     (~5s on CPU)
    4. Save model weights + config + metrics

Requirements:
    pip install sentence-transformers>=3.0

Usage:
    python train_type_heads.py
    python train_type_heads.py --epochs 50 --lr 5e-4
    uv run python -m benchmarks.aap_mcp.train_type_heads
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from torch.utils.data import DataLoader, TensorDataset

HERE = Path(__file__).resolve().parent


# ── Configuration ──────────────────────────────────────────────────────


@dataclass
class Config:
    base_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    epochs: int = 30
    batch_size: int = 256
    learning_rate: float = 1e-3
    dev_fraction: float = 0.1
    seed: int = 42
    data_dir: Path = field(default_factory=lambda: HERE)
    output_dir: Path = field(default_factory=lambda: HERE / "encoder_model")

    def to_dict(self) -> dict:
        d = asdict(self)
        for k, v in d.items():
            if isinstance(v, Path):
                d[k] = str(v)
        return d


# ── Model ──────────────────────────────────────────────────────────────


class TypePredictor(nn.Module):
    """Two linear heads: one for source type, one for target type."""

    def __init__(self, embedding_dim: int, n_types: int):
        super().__init__()
        self.source = nn.Linear(embedding_dim, n_types)
        self.target = nn.Linear(embedding_dim, n_types)

    def forward(self, embeddings):
        return self.source(embeddings), self.target(embeddings)


# ── Data ───────────────────────────────────────────────────────────────


def load_data(data_dir: Path):
    """Load training examples and entity types from disk.

    Returns (examples, entity_types) where:
      - examples: list of {"query", "source_type", "target_type", "style"}
      - entity_types: dict mapping type name → description
    """
    with open(data_dir / "graph_snapshot.json") as f:
        graph = json.load(f)

    examples = []
    with open(data_dir / "training_data.jsonl") as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    return examples, graph["entity_types"]


def prepare_labels(examples, entity_types):
    """Convert raw examples into query list + label tensors.

    Returns (queries, src_labels, tgt_labels, type_names) where:
      - queries: list of query strings
      - src_labels: LongTensor of source type indices
      - tgt_labels: LongTensor of target type indices
      - type_names: sorted list of all 79 type names (index → name)
    """
    type_names = sorted(entity_types.keys())
    type_to_idx = {t: i for i, t in enumerate(type_names)}

    queries, src_indices, tgt_indices = [], [], []
    for ex in examples:
        src, tgt = ex["source_type"], ex["target_type"]
        if src in type_to_idx and tgt in type_to_idx:
            queries.append(ex["query"])
            src_indices.append(type_to_idx[src])
            tgt_indices.append(type_to_idx[tgt])

    return (
        queries,
        torch.tensor(src_indices, dtype=torch.long),
        torch.tensor(tgt_indices, dtype=torch.long),
        type_names,
    )


def encode_queries(base_model: str, queries: list[str]) -> torch.Tensor:
    """Encode all queries with the frozen sentence transformer.

    This is the slowest step (~30s on CPU for ~4000 queries).
    The encoder weights are not updated — we just extract embeddings.
    """
    encoder = SentenceTransformer(base_model)
    embeddings = encoder.encode(queries, show_progress_bar=True, convert_to_numpy=True)
    return torch.tensor(embeddings, dtype=torch.float32)


def make_dataloaders(embeddings, src_labels, tgt_labels, cfg):
    """Split into train/dev and wrap in DataLoaders.

    Returns (train_loader, dev_loader).
    """
    n = len(embeddings)
    random.seed(cfg.seed)
    indices = list(range(n))
    random.shuffle(indices)

    dev_size = int(n * cfg.dev_fraction)
    dev_idx = indices[:dev_size]
    train_idx = indices[dev_size:]

    train_ds = TensorDataset(embeddings[train_idx], src_labels[train_idx], tgt_labels[train_idx])
    dev_ds = TensorDataset(embeddings[dev_idx], src_labels[dev_idx], tgt_labels[dev_idx])

    return (
        DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True),
        DataLoader(dev_ds, batch_size=cfg.batch_size),
    )


# ── Training ───────────────────────────────────────────────────────────


def train_one_epoch(model, loader, optimizer):
    """Run one epoch of training. Returns average loss."""
    model.train()
    total_loss = 0.0

    for emb, src_labels, tgt_labels in loader:
        src_logits, tgt_logits = model(emb)
        loss = (
            F.cross_entropy(src_logits, src_labels)
            + F.cross_entropy(tgt_logits, tgt_labels)
        )
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    return total_loss / len(loader)


@torch.no_grad()
def evaluate(model, loader):
    """Evaluate on dev set. Returns dict with accuracy metrics."""
    model.eval()
    all_src_ok, all_tgt_ok = [], []

    for emb, src_labels, tgt_labels in loader:
        src_logits, tgt_logits = model(emb)
        all_src_ok.append(src_logits.argmax(dim=1) == src_labels)
        all_tgt_ok.append(tgt_logits.argmax(dim=1) == tgt_labels)

    src_ok = torch.cat(all_src_ok)
    tgt_ok = torch.cat(all_tgt_ok)
    return {
        "source_acc": src_ok.float().mean().item(),
        "target_acc": tgt_ok.float().mean().item(),
        "exact_acc": (src_ok & tgt_ok).float().mean().item(),
    }


def train(model, train_loader, dev_loader, optimizer, epochs):
    """Full training loop. Prints per-epoch metrics, returns final metrics."""
    print(f"{'Epoch':>5}  {'Loss':>8}  {'Src':>6}  {'Tgt':>6}  {'Exact':>6}")
    print("─" * 40)

    metrics = {}
    for epoch in range(1, epochs + 1):
        loss = train_one_epoch(model, train_loader, optimizer)
        metrics = {**evaluate(model, dev_loader), "train_loss": loss, "epoch": epoch}
        print(
            f"{epoch:>5}  {loss:>8.4f}  "
            f"{metrics['source_acc']:>5.1%}  "
            f"{metrics['target_acc']:>5.1%}  "
            f"{metrics['exact_acc']:>5.1%}"
        )
    return metrics


# ── Save / Load ────────────────────────────────────────────────────────


def save_model(model, type_names, cfg, metrics):
    """Save heads.pt + config.json + metrics.json to output_dir."""
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    torch.save(
        {
            "model": model.state_dict(),
            "base_model": cfg.base_model,
            "embedding_dim": cfg.embedding_dim,
            "source_types": type_names,
            "target_types": type_names,
        },
        cfg.output_dir / "heads.pt",
    )
    with open(cfg.output_dir / "config.json", "w") as f:
        json.dump(cfg.to_dict(), f, indent=2)
    with open(cfg.output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


def load_model(model_dir: Path):
    """Load encoder + predictor from a saved checkpoint.

    Returns (encoder, predictor, source_types, target_types).
    """
    ckpt = torch.load(model_dir / "heads.pt", weights_only=True)
    encoder = SentenceTransformer(ckpt["base_model"])
    predictor = TypePredictor(ckpt["embedding_dim"], len(ckpt["source_types"]))
    predictor.load_state_dict(ckpt["model"])
    predictor.eval()
    return encoder, predictor, ckpt["source_types"], ckpt["target_types"]


# ── Main ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Train type-prediction heads")
    parser.add_argument("--base-model", default=Config.base_model)
    parser.add_argument("--epochs", type=int, default=Config.epochs)
    parser.add_argument("--batch-size", type=int, default=Config.batch_size)
    parser.add_argument("--lr", type=float, default=Config.learning_rate)
    parser.add_argument("--seed", type=int, default=Config.seed)
    args = parser.parse_args()

    cfg = Config(
        base_model=args.base_model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        seed=args.seed,
    )
    torch.manual_seed(cfg.seed)
    random.seed(cfg.seed)

    # ── Data ───────────────────────────────────────────────────────

    print("Loading data...")
    examples, entity_types = load_data(cfg.data_dir)
    queries, src_labels, tgt_labels, type_names = prepare_labels(examples, entity_types)
    print(f"  Examples: {len(queries)},  Types: {len(type_names)}")

    # ── Encode ─────────────────────────────────────────────────────

    print(f"\nEncoding {len(queries)} queries with {cfg.base_model}...")
    embeddings = encode_queries(cfg.base_model, queries)
    cfg.embedding_dim = embeddings.shape[1]
    print(f"  Shape: {list(embeddings.shape)}")

    # ── Split ──────────────────────────────────────────────────────

    train_loader, dev_loader = make_dataloaders(
        embeddings, src_labels, tgt_labels, cfg,
    )
    print(f"  Train: {len(train_loader.dataset)},  Dev: {len(dev_loader.dataset)}")

    # ── Train ──────────────────────────────────────────────────────

    model = TypePredictor(cfg.embedding_dim, len(type_names))
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.learning_rate)

    print(f"\nTypePredictor({cfg.embedding_dim} -> {len(type_names)})")
    print(f"  Epochs: {cfg.epochs}  Batch: {cfg.batch_size}  LR: {cfg.learning_rate}\n")

    metrics = train(model, train_loader, dev_loader, optimizer, cfg.epochs)

    # ── Save ───────────────────────────────────────────────────────

    save_model(model, type_names, cfg, metrics)
    print(f"\nSaved to {cfg.output_dir}/")
    print(f"  heads.pt, config.json, metrics.json")


if __name__ == "__main__":
    main()
