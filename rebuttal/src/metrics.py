"""Metrics: DSPy per-example metric (for the optimizer) + macro-F1 / confusion."""
from collections import defaultdict
from src.data import LABELS


def dspy_metric(example, pred, trace=None):
    """1.0 if predicted reaction matches gold, else 0.0 (unweighted)."""
    try:
        return float(pred.reaction == example.reaction)
    except Exception:
        return 0.0


def make_weighted_metric(trainset):
    """Balanced class-weighted metric for MIPROv2 so the optimizer is rewarded
    for getting rare classes (esp. 'lower') right. weight_c = N / (K * count_c),
    i.e. sklearn's class_weight='balanced'. Returns w_c if correct else 0.0."""
    counts = {lab: 0 for lab in LABELS}
    for e in trainset:
        counts[e.reaction] = counts.get(e.reaction, 0) + 1
    n, k = sum(counts.values()), len(LABELS)
    weight = {lab: (n / (k * counts[lab]) if counts[lab] else 0.0) for lab in LABELS}

    def metric(example, pred, trace=None):
        try:
            if pred.reaction != example.reaction:
                return 0.0
            w = weight.get(example.reaction, 1.0)
            # in trace mode (bootstrapping demos) DSPy expects a bool
            return (w > 0) if trace is not None else w
        except Exception:
            return False if trace is not None else 0.0

    return metric, weight


def macro_f1(golds, preds):
    """Return (macro_f1, per_class dict, confusion matrix, accuracy)."""
    per = {}
    f1s = []
    for lab in LABELS:
        tp = sum(1 for g, p in zip(golds, preds) if g == lab and p == lab)
        fp = sum(1 for g, p in zip(golds, preds) if g != lab and p == lab)
        fn = sum(1 for g, p in zip(golds, preds) if g == lab and p != lab)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        support = sum(1 for g in golds if g == lab)
        per[lab] = {"precision": prec, "recall": rec, "f1": f1, "support": support}
        if support > 0:                      # macro over classes PRESENT in gold only
            f1s.append(f1)
    acc = sum(1 for g, p in zip(golds, preds) if g == p) / len(golds) if golds else 0.0
    conf = defaultdict(lambda: defaultdict(int))
    for g, p in zip(golds, preds):
        conf[g][p] += 1
    return sum(f1s) / len(f1s), per, conf, acc


def print_report(name, golds, preds):
    mf1, per, conf, acc = macro_f1(golds, preds)
    print(f"\n===== {name} =====")
    print(f"macro-F1 = {mf1:.3f} | accuracy = {acc:.3f} | n = {len(golds)}")
    print(f"{'class':>6} {'prec':>6} {'rec':>6} {'f1':>6} {'supp':>5}")
    for lab in LABELS:
        d = per[lab]
        print(f"{lab:>6} {d['precision']:6.2f} {d['recall']:6.2f} "
              f"{d['f1']:6.2f} {d['support']:5d}")
    print("confusion (rows=gold, cols=pred):")
    print(f"{'':>6}" + "".join(f"{l:>6}" for l in LABELS))
    for g in LABELS:
        print(f"{g:>6}" + "".join(f"{conf[g][p]:6d}" for p in LABELS))
    return mf1, acc
