"""轻量 DAG 工具:拓扑排序 / 防环校验 / 上下游查询。

图结构(前端 X6 画布产出,存 dag_graph.graph):
    {
      "nodes": [{ "node_key", "name", "template_code", "params", "pos": {...},
                  "retry", "countdown", "error_policy": "fail_fast|continue" }],
      "edges": [{ "source": node_key, "target": node_key, "condition"?: ... }],
      "viewport": {...}
    }
"""

from typing import Any


class DAG:
    """有向无环图。graph: {node_key: [下游 node_key,...]}。"""

    def __init__(self) -> None:
        self.graph: dict[str, list[str]] = {}

    def add_node(self, node: str) -> None:
        if node not in self.graph:
            self.graph[node] = []

    def add_edge(self, src: str, dst: str) -> None:
        if src not in self.graph or dst not in self.graph:
            raise ValueError(f'边引用了不存在的节点: {src} -> {dst}')
        if dst not in self.graph[src]:
            self.graph[src].append(dst)
        # 加边即校验无环
        if not self._is_acyclic():
            self.graph[src].remove(dst)
            raise ValueError(f'存在环路: {src} -> {dst}')

    def predecessors(self, node: str) -> list[str]:
        return [n for n, downs in self.graph.items() if node in downs]

    def downstream(self, node: str) -> list[str]:
        return list(self.graph.get(node, []))

    def ind_nodes(self) -> list[str]:
        """入度为 0 的根节点。"""
        has_pred = {d for downs in self.graph.values() for d in downs}
        return [n for n in self.graph if n not in has_pred]

    def all_downstreams(self, node: str) -> list[str]:
        """node 的所有(递归)下游。"""
        seen: list[str] = []
        stack = list(self.downstream(node))
        while stack:
            n = stack.pop()
            if n not in seen:
                seen.append(n)
                stack.extend(self.downstream(n))
        return seen

    def _is_acyclic(self) -> bool:
        try:
            self.topological_sort()
            return True
        except ValueError:
            return False

    def topological_sort(self) -> list[str]:
        in_deg = dict.fromkeys(self.graph, 0)
        for downs in self.graph.values():
            for d in downs:
                in_deg[d] += 1
        queue = [n for n, d in in_deg.items() if d == 0]
        order: list[str] = []
        while queue:
            n = queue.pop(0)
            order.append(n)
            for d in self.graph[n]:
                in_deg[d] -= 1
                if in_deg[d] == 0:
                    queue.append(d)
        if len(order) != len(self.graph):
            raise ValueError('图中存在环路')
        return order


def build_dag(graph: dict[str, Any]) -> DAG:
    """从图 JSON 构造 DAG(并校验无环)。"""
    dag = DAG()
    nodes = graph.get('nodes') or []
    edges = graph.get('edges') or []
    for nd in nodes:
        dag.add_node(nd['node_key'])
    for e in edges:
        dag.add_edge(e['source'], e['target'])
    dag.topological_sort()  # 触发校验
    return dag


def validate_graph(graph: dict[str, Any]) -> tuple[bool, str]:
    """校验图合法(节点唯一、边引用存在、无环)。返回 (ok, message)。"""
    try:
        nodes = graph.get('nodes') or []
        keys = [n.get('node_key') for n in nodes]
        if not keys:
            return False, '图中没有节点'
        if len(keys) != len(set(keys)):
            return False, '存在重复的节点 key'
        if any(not n.get('template_code') for n in nodes):
            return False, '存在未配置模板的节点'
        build_dag(graph)
        return True, 'ok'
    except Exception as e:
        return False, str(e)
