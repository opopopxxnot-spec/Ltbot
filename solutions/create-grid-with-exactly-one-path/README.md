# Create Grid With Exactly One Path (Easy)

- **Problem URL:** https://leetcode.com/problems/create-grid-with-exactly-one-path/
- **Language:** CPP
- **Runtime:** 1 ms (Beats 57.2%)
- **Date:** 2026-10-27 05:25:12 UTC

```cpp
#include <vector>
#include <string>

using namespace std;

class Solution {
public:
    vector<string> createGrid(int m, int n) {
        vector<string> grid(m, string(n, '#'));
        for (int i = 0; i < m; ++i) {
            grid[i][0] = '.';
        }
        for (int j = 0; j < n; ++j) {
            grid[m - 1][j] = '.';
        }
        return grid;
    }
};
```
