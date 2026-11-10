#!/usr/bin/env python3
"""述职提问小游戏：随机抽题作答，按相似度判分，低于阈值不通过。

相似度 = 要点覆盖率 * 0.8 + 文本相似度 * 0.2
- 要点覆盖率：参考答案拆成若干要点，回答中命中任一关键词即算覆盖该要点
- 文本相似度：回答与参考答案的字符二元组 Dice 系数

用法：
    python3 shuzhi_game.py              # 随机 5 题
    python3 shuzhi_game.py -n 10        # 随机 10 题
    python3 shuzhi_game.py --all        # 全部题目，随机顺序
    python3 shuzhi_game.py --threshold 0.8 --seed 1
作答时可输入多行，单独输入空行结束；输入 :skip 跳过，:q 退出。
"""
import argparse
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
POINT_WEIGHT = 0.8
TEXT_WEIGHT = 0.2


def normalize(s):
    s = s.lower()
    s = s.replace("％", "%").replace("＋", "+")
    return re.sub(r"[\s，。、；：,.;:!?！？“”\"'（）()\[\]【】<>《》\-_/]+", "", s)


def bigrams(s):
    return [s[i:i + 2] for i in range(len(s) - 1)] if len(s) > 1 else [s]


def dice(a, b):
    ga, gb = bigrams(a), bigrams(b)
    if not ga or not gb:
        return 0.0
    pool = {}
    for g in gb:
        pool[g] = pool.get(g, 0) + 1
    hit = 0
    for g in ga:
        if pool.get(g, 0) > 0:
            hit += 1
            pool[g] -= 1
    return 2 * hit / (len(ga) + len(gb))


def score(answer, item):
    ans = normalize(answer)
    hit, miss = [], []
    for p in item["points"]:
        if any(normalize(k) in ans for k in p["keywords"]):
            hit.append(p["name"])
        else:
            miss.append(p["name"])
    coverage = len(hit) / len(item["points"])
    text_sim = dice(ans, normalize(item["answer"]))
    total = coverage * POINT_WEIGHT + text_sim * TEXT_WEIGHT
    return total, coverage, text_sim, hit, miss


def read_answer():
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() in (":q", ":skip") and not lines:
            return line.strip()
        if line.strip() == "":
            if lines:
                break
            continue
        lines.append(line)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="述职提问小游戏")
    ap.add_argument("-n", type=int, default=5, help="抽题数量，默认 5")
    ap.add_argument("--all", action="store_true", help="抽取全部题目")
    ap.add_argument("--threshold", type=float, default=0.8, help="通过阈值，默认 0.8")
    ap.add_argument("--seed", type=int, help="随机种子，便于复现")
    ap.add_argument("--file", default=os.path.join(HERE, "shuzhi_questions.json"), help="题库路径")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8") as f:
        bank = json.load(f)
    rng = random.Random(args.seed)
    picked = rng.sample(bank, len(bank) if args.all else min(args.n, len(bank)))

    print(f"述职提问开始，共 {len(picked)} 题，相似度 ≥ {args.threshold:.0%} 为通过。")
    print("作答可输入多行，单独输入空行结束；:skip 跳过，:q 退出。\n")

    results = []
    for i, item in enumerate(picked, 1):
        print("=" * 60)
        print(f"第 {i}/{len(picked)} 题 [{item['category']}]")
        print(item["question"])
        print("-" * 60)
        ans = read_answer()
        if ans == ":q":
            break
        if ans == ":skip" or not ans.strip():
            total, coverage, text_sim, hit, miss = 0.0, 0.0, 0.0, [], [p["name"] for p in item["points"]]
        else:
            total, coverage, text_sim, hit, miss = score(ans, item)
        passed = total >= args.threshold
        results.append((item, total, passed))

        print("-" * 60)
        print(f"相似度 {total:.1%}（要点覆盖 {coverage:.0%}，文本相似 {text_sim:.0%}） → {'通过' if passed else '不通过'}")
        if hit:
            print("已答到：" + "、".join(hit))
        if miss:
            print("缺少：" + "、".join(miss))
        if not passed:
            print("参考答案：" + item["answer"])
        print()

    if not results:
        return
    n_pass = sum(1 for _, _, p in results if p)
    avg = sum(s for _, s, _ in results) / len(results)
    print("=" * 60)
    print(f"结束：{n_pass}/{len(results)} 题通过，平均相似度 {avg:.1%}")
    for item, s, p in results:
        print(f"  [{'通过' if p else '未过'}] {s:6.1%}  {item['question']}")
    sys.exit(0 if n_pass == len(results) else 1)


if __name__ == "__main__":
    main()
