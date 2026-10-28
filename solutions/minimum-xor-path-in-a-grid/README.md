# Minimum XOR Path in a Grid (Medium)

- **Problem URL:** https://leetcode.com/problems/minimum-xor-path-in-a-grid/
- **Language:** CPP
- **Runtime:** 87 ms (Beats 98.3%)
- **Date:** 2026-10-28 06:02:12 UTC

```cpp
#include <vector>
#include <bitset>

using namespace std;

class Solution {
public:
    int minCost(vector<vector<int>>& grid) {
        int m = grid.size();
        int n = grid[0].size();
        
        vector<bitset<1024>> dp(n);
        
        for (int i = 0; i < m; ++i) {
            vector<bitset<1024>> next_dp(n);
            for (int j = 0; j < n; ++j) {
                if (i == 0 && j == 0) {
                    next_dp[0].set(grid[0][0]);
                    continue;
                }
                bitset<1024> prev;
                if (i > 0) {
                    prev |= dp[j];
                }
                if (j > 0) {
                    prev |= next_dp[j - 1];
                }
                
                int val = grid[i][j];
                for (int x = 0; x < 1024; ++x) {
                    if (prev.test(x)) {
                        next_dp[j].set(x ^ val);
                    }
                }
            }
            dp = move(next_dp);
        }
        
        for (int x = 0; x < 1024; ++x) {
            if (dp[n - 1].test(x)) {
                return x;
            }
        }
        
        return 0;
    }
};
```
