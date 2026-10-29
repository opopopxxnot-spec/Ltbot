#include <vector>
#include <string>

using namespace std;

class Solution {
    int timer;
    vector<int> tin, tout;
    vector<int> depth;
    vector<vector<int>> up;
    vector<vector<int>> adj;
    vector<int> bit;
    int max_time;

    void add_bit(int idx, int val) {
        for (; idx <= max_time; idx += idx & -idx) {
            bit[idx] ^= val;
        }
    }

    int query_bit(int idx) {
        int sum = 0;
        for (; idx > 0; idx -= idx & -idx) {
            sum ^= bit[idx];
        }
        return sum;
    }

    void dfs(int u, int p, int d, const string& s) {
        tin[u] = ++timer;
        depth[u] = d;
        up[u][0] = p;
        for (int i = 1; i < 17; ++i) {
            up[u][i] = up[up[u][i - 1]][i - 1];
        }

        for (int v : adj[u]) {
            if (v != p) {
                dfs(v, u, d + 1, s);
            }
        }
        tout[u] = timer;
    }

    int get_lca(int u, int v) {
        if (depth[u] < depth[v]) swap(u, v);
        for (int i = 16; i >= 0; --i) {
            if (depth[u] - (1 << i) >= depth[v]) {
                u = up[u][i];
            }
        }
        if (u == v) return u;
        for (int i = 16; i >= 0; --i) {
            if (up[u][i] != up[v][i]) {
                u = up[u][i];
                v = up[v][i];
            }
        }
        return up[u][0];
    }

    void update_node(int u, int delta) {
        add_bit(tin[u], delta);
        add_bit(tout[u] + 1, delta);
    }

public:
    vector<bool> palindromePath(int n, vector<vector<int>>& edges, string s, vector<string>& queries) {
        adj.assign(n, vector<int>());
        for (const auto& edge : edges) {
            adj[edge[0]].push_back(edge[1]);
            adj[edge[1]].push_back(edge[0]);
        }

        timer = 0;
        tin.resize(n);
        tout.resize(n);
        depth.resize(n);
        up.assign(n, vector<int>(17));

        dfs(0, 0, 0, s);

        max_time = n + 2;
        bit.assign(max_time + 1, 0);

        for (int i = 0; i < n; ++i) {
            int mask = 1 << (s[i] - 'a');
            update_node(i, mask);
        }

        vector<bool> ans;
        for (const string& q : queries) {
            if (q[0] == 'u') {
                int u = 0;
                int idx = 7;
                while (q[idx] != ' ') {
                    u = u * 10 + (q[idx] - '0');
                    idx++;
                }
                idx++;
                char c = q[idx];
                if (s[u] != c) {
                    int delta = (1 << (s[u] - 'a')) ^ (1 << (c - 'a'));
                    s[u] = c;
                    update_node(u, delta);
                }
            } else {
                int u = 0;
                int idx = 6;
                while (q[idx] != ' ') {
                    u = u * 10 + (q[idx] - '0');
                    idx++;
                }
                idx++;
                int v = 0;
                while (idx < (int)q.size()) {
                    v = v * 10 + (q[idx] - '0');
                    idx++;
                }

                int lca = get_lca(u, v);
                int mask_u = query_bit(tin[u]);
                int mask_v = query_bit(tin[v]);
                int lca_mask = 1 << (s[lca] - 'a');
                int path_mask = mask_u ^ mask_v ^ lca_mask;

                ans.push_back((path_mask & (path_mask - 1)) == 0);
            }
        }

        return ans;
    }
};