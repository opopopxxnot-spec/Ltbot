# Shortest Path With At Most K Consecutive Identical Characters (Medium)

- **Problem URL:** https://leetcode.com/problems/shortest-path-with-at-most-k-consecutive-identical-characters/
- **Language:** CPP
- **Runtime:** 212 ms (Beats 66.9%)
- **Date:** 2026-10-30 06:08:55 UTC

```cpp
#include <vector>
#include <queue>
#include <tuple>

using namespace std;

class Solution {
public:
    int shortestPath(int n, vector<vector<int>>& edges, string labels, int k) {
        if (n <= 1) return 0;

        vector<vector<pair<int, int>>> same_adj(n);
        vector<vector<pair<int, int>>> diff_adj(n);

        for (const auto& edge : edges) {
            int u = edge[0];
            int v = edge[1];
            int w = edge[2];
            if (labels[u] == labels[v]) {
                same_adj[u].emplace_back(v, w);
            } else {
                diff_adj[u].emplace_back(v, w);
            }
        }

        // dist[u][c] is the shortest distance to reach node u with c consecutive labels[u]
        // c ranges from 1 to k
        const int INF = 1e9 + 7;
        vector<vector<int>> dist(n, vector<int>(k + 1, INF));
        vector<bool> diff_relaxed(n, false);

        // min-heap storing {distance, u, count}
        using State = tuple<int, int, int>;
        priority_queue<State, vector<State>, greater<State>> pq;

        dist[0][1] = 0;
        pq.emplace(0, 0, 1);

        while (!pq.empty()) {
            auto [d, u, c] = pq.top();
            pq.pop();

            if (d > dist[u][c]) continue;

            if (u == n - 1) {
                return d;
            }

            // Relax different-label edges only the first time node u is popped
            if (!diff_relaxed[u]) {
                diff_relaxed[u] = true;
                for (const auto& [v, w] : diff_adj[u]) {
                    if (d + w < dist[v][1]) {
                        dist[v][1] = d + w;
                        pq.emplace(dist[v][1], v, 1);
                    }
                }
            }

            // Relax same-label edges if count < k
            if (c < k) {
                for (const auto& [v, w] : same_adj[u]) {
                    if (d + w < dist[v][c + 1]) {
                        dist[v][c + 1] = d + w;
                        pq.emplace(dist[v][c + 1], v, c + 1);
                    }
                }
            }
        }

        return -1;
    }
};
```
