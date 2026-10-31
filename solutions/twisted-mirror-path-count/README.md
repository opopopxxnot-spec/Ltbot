# Twisted Mirror Path Count (Medium)

- **Problem URL:** https://leetcode.com/problems/twisted-mirror-path-count/
- **Language:** CPP
- **Runtime:** 165 ms (Beats 45.0%)
- **Date:** 2026-10-31 06:04:30 UTC

```cpp
#include <vector>

using namespace std;

class Solution {
public:
    int uniquePaths(vector<vector<int>>& grid) {
        int m = grid.size();
        int n = grid[0].size();
        const int MOD = 1e9 + 7;

        // nxt[r][c][dir] stores {dest_r, dest_c} if a robot attempts to enter (r, c) with direction dir
        // dir: 0 = RIGHT, 1 = DOWN
        // Packed as int: (r << 16) | c, or -1 if out of bounds.
        vector<vector<array<int, 2>>> nxt(m, vector<array<int, 2>>(n));
        vector<vector<int>> dp(m, vector<int>(n, 0));

        for (int r = m - 1; r >= 0; --r) {
            for (int c = n - 1; c >= 0; --c) {
                for (int dir = 0; dir < 2; ++dir) {
                    if (grid[r][c] == 0) {
                        nxt[r][c][dir] = (r << 16) | c;
                    } else {
                        if (dir == 0) { // entered moving RIGHT -> turned DOWN
                            if (r + 1 < m) {
                                nxt[r][c][dir] = nxt[r + 1][c][1];
                            } else {
                                nxt[r][c][dir] = -1;
                            }
                        } else { // entered moving DOWN -> turned RIGHT
                            if (c + 1 < n) {
                                nxt[r][c][dir] = nxt[r][c + 1][0];
                            } else {
                                nxt[r][c][dir] = -1;
                            }
                        }
                    }
                }

                if (grid[r][c] == 0) {
                    if (r == m - 1 && c == n - 1) {
                        dp[r][c] = 1;
                    } else {
                        long long ways = 0;
                        // Move RIGHT
                        if (c + 1 < n) {
                            int target = nxt[r][c + 1][0];
                            if (target != -1) {
                                int tr = target >> 16;
                                int tc = target & 0xFFFF;
                                ways += dp[tr][tc];
                            }
                        }
                        // Move DOWN
                        if (r + 1 < m) {
                            int target = nxt[r + 1][c][1];
                            if (target != -1) {
                                int tr = target >> 16;
                                int tc = target & 0xFFFF;
                                ways += dp[tr][tc];
                            }
                        }
                        dp[r][c] = ways % MOD;
                    }
                }
            }
        }

        return dp[0][0];
    }
};
```
