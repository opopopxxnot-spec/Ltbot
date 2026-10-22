# Minimum Operations to Sort a Permutation (Medium)

- **Problem URL:** https://leetcode.com/problems/minimum-operations-to-sort-a-permutation/
- **Language:** CPP
- **Runtime:** 29 ms (Beats 9.8%)
- **Date:** 2026-10-22 05:09:35 UTC

```cpp
#include <vector>
#include <queue>

using namespace std;

class Solution {
public:
    int minOperations(vector<int>& nums) {
        int n = nums.size();
        if (n <= 1) return 0;

        int p = -1;
        for (int i = 0; i < n; ++i) {
            if (nums[i] == 0) {
                p = i;
                break;
            }
        }

        bool is_inc = true;
        for (int i = 0; i < n; ++i) {
            if (nums[(p + i) % n] != i) {
                is_inc = false;
                break;
            }
        }

        bool is_dec = true;
        for (int i = 0; i < n; ++i) {
            if (nums[(p - i + n) % n] != i) {
                is_dec = false;
                break;
            }
        }

        if (!is_inc && !is_dec) return -1;

        // BFS to find the shortest path
        // State: (ori, pos), where ori = 0 (+1, increasing), ori = 1 (-1, decreasing)
        // pos is the current index of 0.
        // Total states = 2 * n.
        // Target state: ori = 0, pos = 0.
        
        vector<int> dist(2 * n, -1);
        queue<int> q;

        auto add_start = [&](int ori, int pos) {
            int u = ori * n + pos;
            if (dist[u] == -1) {
                dist[u] = 0;
                q.push(u);
            }
        };

        if (is_inc) add_start(0, p);
        if (is_dec) add_start(1, p);

        while (!q.empty()) {
            int u = q.front();
            q.pop();

            int ori = u / n;
            int pos = u % n;

            if (ori == 0 && pos == 0) {
                return dist[u];
            }

            // Op 1: Rotate Left
            int next_pos_rot = (pos - 1 + n) % n;
            int v_rot = ori * n + next_pos_rot;
            if (dist[v_rot] == -1) {
                dist[v_rot] = dist[u] + 1;
                q.push(v_rot);
            }

            // Op 2: Reverse
            int next_ori_rev = 1 - ori;
            int next_pos_rev = n - 1 - pos;
            int v_rev = next_ori_rev * n + next_pos_rev;
            if (dist[v_rev] == -1) {
                dist[v_rev] = dist[u] + 1;
                q.push(v_rev);
            }
        }

        return -1;
    }
};
```
