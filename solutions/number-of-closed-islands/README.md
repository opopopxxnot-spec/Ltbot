# Number of Closed Islands (Medium)

- **Problem URL:** https://leetcode.com/problems/number-of-closed-islands/
- **Language:** CPP
- **Runtime:** 0 ms (Beats 100%)
- **Date:** 2026-10-25 05:04:57 UTC

```cpp
#include <vector>

using namespace std;

class Solution {
public:
    int closedIsland(vector<vector<int>>& grid) {
        int m = grid.size();
        int n = grid[0].size();

        auto dfs = [&](auto self, int r, int c) -> void {
            if (r < 0 || r >= m || c < 0 || c >= n || grid[r][c] != 0) {
                return;
            }
            grid[r][c] = 1;
            self(self, r + 1, c);
            self(self, r - 1, c);
            self(self, r, c + 1);
            self(self, r, c - 1);
        };

        for (int i = 0; i < m; ++i) {
            if (grid[i][0] == 0) dfs(dfs, i, 0);
            if (grid[i][n - 1] == 0) dfs(dfs, i, n - 1);
        }
        for (int j = 0; j < n; ++j) {
            if (grid[0][j] == 0) dfs(dfs, 0, j);
            if (grid[m - 1][j] == 0) dfs(dfs, m - 1, j);
        }

        int count = 0;
        for (int i = 1; i < m - 1; ++i) {
            for (int j = 1; j < n - 1; ++j) {
                if (grid[i][j] == 0) {
                    count++;
                    dfs(dfs, i, j);
                }
            }
        }

        return count;
    }
};
```
