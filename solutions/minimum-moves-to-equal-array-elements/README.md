# Minimum Moves to Equal Array Elements (Medium)

- **Problem URL:** https://leetcode.com/problems/minimum-moves-to-equal-array-elements/
- **Language:** CPP
- **Runtime:** 0 ms (Beats 100%)
- **Date:** 2026-11-01 06:35:18 UTC

```cpp
#include <vector>
#include <algorithm>
#include <numeric>

class Solution {
public:
    int minMoves(std::vector<int>& nums) {
        int min_val = *std::min_element(nums.begin(), nums.end());
        long long moves = 0;
        for (int x : nums) {
            moves += (x - min_val);
        }
        return static_cast<int>(moves);
    }
};
```
