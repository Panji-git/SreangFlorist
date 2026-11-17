"""
Python Native FP-Growth & Association Rule Mining Module.
Constructs an FP-Tree and mines frequent itemsets and association rules
without requiring heavy external data science libraries.
Calculates Support, Confidence, and Lift Ratio.
"""

from collections import defaultdict
from itertools import combinations
import sqlite3
from typing import Dict, List, Tuple, Any, Optional


class FPNode:
    """A node in the FP-Tree."""

    def __init__(self, item: Optional[str], count: int = 1, parent: Optional["FPNode"] = None):
        self.item = item
        self.count = count
        self.parent = parent
        self.children: Dict[str, "FPNode"] = {}
        self.node_link: Optional["FPNode"] = None

    def increment(self, count: int = 1):
        self.count += count


class FPTree:
    """FP-Tree structure for mining frequent patterns."""

    def __init__(self, transactions: List[List[str]], min_sup_count: int):
        self.min_sup_count = min_sup_count
        self.item_counts: Dict[str, int] = defaultdict(int)

        # 1. First pass: count frequencies
        for transaction in transactions:
            for item in transaction:
                self.item_counts[item] += 1

        # Filter items by min_sup_count
        self.frequent_items = {
            item: count
            for item, count in self.item_counts.items()
            if count >= self.min_sup_count
        }

        # Header table: maps item -> (count, first_node)
        self.header_table: Dict[str, Tuple[int, Optional[FPNode]]] = {
            item: (count, None) for item, count in self.frequent_items.items()
        }

        # Root node
        self.root = FPNode(item=None, count=1, parent=None)

        # 2. Second pass: insert transactions into FP-Tree
        for transaction in transactions:
            # Sort items in transaction by descending frequency
            sorted_items = [
                item for item in transaction if item in self.frequent_items
            ]
            sorted_items.sort(
                key=lambda x: (self.frequent_items[x], x), reverse=True
            )

            if sorted_items:
                self._insert_tree(sorted_items, self.root)

    def _insert_tree(self, items: List[str], current_node: FPNode):
        first_item = items[0]
        if first_item in current_node.children:
            current_node.children[first_item].increment(1)
        else:
            new_node = FPNode(item=first_item, count=1, parent=current_node)
            current_node.children[first_item] = new_node

            # Update header table link
            count, head = self.header_table[first_item]
            if head is None:
                self.header_table[first_item] = (count, new_node)
            else:
                curr = head
                while curr.node_link is not None:
                    curr = curr.node_link
                curr.node_link = new_node

        if len(items) > 1:
            self._insert_tree(items[1:], current_node.children[first_item])

    def find_prefix_paths(self, item: str) -> Dict[Tuple[str, ...], int]:
        """Find conditional pattern base for an item."""
        conditional_patterns: Dict[Tuple[str, ...], int] = {}
        _, node = self.header_table.get(item, (0, None))

        while node is not None:
            prefix_path = []
            parent = node.parent
            while parent is not None and parent.item is not None:
                prefix_path.append(parent.item)
                parent = parent.parent

            if prefix_path:
                prefix_path.reverse()
                conditional_patterns[tuple(prefix_path)] = node.count

            node = node.node_link

        return conditional_patterns


def mine_fp_tree(
    tree: FPTree,
    prefix: List[str],
    frequent_itemsets: Dict[frozenset, int],
    min_sup_count: int,
):
    """Recursively mine frequent itemsets from FP-Tree."""
    # Sort items in header table by ascending frequency
    items = sorted(
        tree.header_table.keys(),
        key=lambda x: (tree.header_table[x][0], x)
    )

    for item in items:
        new_prefix = prefix + [item]
        support_count = tree.header_table[item][0]
        frequent_itemsets[frozenset(new_prefix)] = support_count

        # Build conditional pattern base
        prefix_paths = tree.find_prefix_paths(item)
        cond_transactions = []
        for path, count in prefix_paths.items():
            for _ in range(count):
                cond_transactions.append(list(path))

        if cond_transactions:
            cond_tree = FPTree(cond_transactions, min_sup_count)
            if cond_tree.frequent_items:
                mine_fp_tree(
                    cond_tree, new_prefix, frequent_itemsets, min_sup_count
                )


def run_fpgrowth(
    transactions: List[List[str]],
    min_support: float = 0.15,
    min_confidence: float = 0.5,
) -> Dict[str, Any]:
    """
    Executes FP-Growth and extracts Frequent Itemsets and Association Rules.
    Returns:
        dict with:
            - 'total_transactions': int
            - 'frequent_itemsets': list of dicts (itemset, support, count)
            - 'rules': list of dicts (antecedent, consequent, support, confidence, lift)
    """
    n = len(transactions)
    if n == 0:
        return {
            "total_transactions": 0,
            "frequent_itemsets": [],
            "rules": [],
        }

    min_sup_count = max(1, int(min_support * n))
    fp_tree = FPTree(transactions, min_sup_count)

    frequent_patterns: Dict[frozenset, int] = {}
    mine_fp_tree(fp_tree, [], frequent_patterns, min_sup_count)

    # Format frequent itemsets
    itemsets_list = []
    for itemset, count in frequent_patterns.items():
        itemsets_list.append({
            "itemset": sorted(list(itemset)),
            "count": count,
            "support": round(count / n, 4),
            "length": len(itemset),
        })

    # Sort itemsets by length descending then support descending
    itemsets_list.sort(key=lambda x: (x["length"], x["support"]), reverse=True)

    # Generate association rules
    rules = []
    for itemset, count in frequent_patterns.items():
        if len(itemset) >= 2:
            items_list = list(itemset)
            support_both = count / n

            # Check all non-empty subsets
            for k in range(1, len(items_list)):
                for ant_comb in combinations(items_list, k):
                    antecedent = frozenset(ant_comb)
                    consequent = itemset - antecedent

                    ant_count = frequent_patterns.get(antecedent)
                    if not ant_count:
                        # Count from transactions directly if not in frequent patterns
                        ant_count = sum(
                            1 for t in transactions if antecedent.issubset(set(t))
                        )

                    con_count = frequent_patterns.get(consequent)
                    if not con_count:
                        con_count = sum(
                            1 for t in transactions if consequent.issubset(set(t))
                        )

                    if ant_count and ant_count > 0 and con_count and con_count > 0:
                        conf = count / ant_count
                        sup_con = con_count / n
                        lift = conf / sup_con if sup_con > 0 else 0

                        if conf >= min_confidence:
                            rules.append({
                                "antecedent": sorted(list(antecedent)),
                                "consequent": sorted(list(consequent)),
                                "support": round(support_both, 4),
                                "confidence": round(conf, 4),
                                "lift": round(lift, 4),
                                "count": count,
                            })

    # Sort rules by lift descending, then confidence descending
    rules.sort(key=lambda r: (r["lift"], r["confidence"], r["support"]), reverse=True)

    return {
        "total_transactions": n,
        "min_support": min_support,
        "min_confidence": min_confidence,
        "frequent_itemsets": itemsets_list,
        "rules": rules,
    }


def get_association_recommendations(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Extracts completed transactions from database, runs FP-Growth, and formats
    the best recommendation for the catalog studio.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT o.id, ma.id as attr_id, ma.name, ma.category
        FROM orders o
        JOIN order_customizations oc ON o.id = oc.order_id
        JOIN master_attributes ma ON oc.attribute_id = ma.id
        WHERE o.status = 'Selesai'
        ORDER BY o.id
        """
    )
    rows = cursor.fetchall()

    transactions_dict: Dict[str, List[str]] = defaultdict(list)
    attr_meta: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        order_id = row["id"]
        attr_name = row["name"]
        transactions_dict[order_id].append(attr_name)
        if attr_name not in attr_meta:
            attr_meta[attr_name] = {
                "id": row["attr_id"],
                "category": row["category"],
            }

    transactions = list(transactions_dict.values())
    if not transactions:
        return {
            "has_recommendation": False,
            "message": "Belum ada transaksi 'Selesai' untuk menghasilkan rekomendasi.",
            "rule": None,
            "recommended_combination": [],
        }

    # Run FP-Growth
    analysis = run_fpgrowth(transactions, min_support=0.20, min_confidence=0.60)
    rules = analysis["rules"]
    itemsets = analysis["frequent_itemsets"]

    # Find the top 4-item or 3-item frequent combo
    top_combo = None
    for itemset in itemsets:
        if itemset["length"] == 4:
            top_combo = itemset
            break
    if not top_combo and itemsets:
        top_combo = itemsets[0]

    # Best rule
    top_rule = rules[0] if rules else None

    recommendation_items = []
    if top_combo:
        for item_name in top_combo["itemset"]:
            meta = attr_meta.get(item_name, {})
            recommendation_items.append({
                "id": meta.get("id"),
                "name": item_name,
                "category": meta.get("category"),
            })

    return {
        "has_recommendation": len(recommendation_items) > 0,
        "title": "Rekomendasi Spesial Untuk Anda",
        "badge": "Pilihan Terfavorit Atelier",
        "description": "Kombinasi buket elegan yang paling sering dirangkai bersama dan dicintai oleh pelanggan kami.",
        "support": top_combo["support"] if top_combo else 0.0,
        "count": top_combo["count"] if top_combo else 0,
        "lift": top_rule["lift"] if top_rule else 1.0,
        "confidence": top_rule["confidence"] if top_rule else 1.0,
        "items": recommendation_items,
        "total_mined_transactions": len(transactions),
        "total_rules_found": len(rules),
    }
