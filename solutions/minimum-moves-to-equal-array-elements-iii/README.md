# Minimum Moves to Equal Array Elements III (Easy)

- **Problem URL:** https://leetcode.com/problems/minimum-moves-to-equal-array-elements-iii/
- **Language:** CPP
- **Runtime:** 1 ms (Beats 30.0%)
- **Date:** 2026-11-03 20:36:36 UTC

```cpp
class Solution {
public:
    int minMoves(vector<int>& nums) {
        int max_val = *max_element(nums.begin(), nums.end());
        int moves = 0;
        for (int x : nums) {
            moves += max_val - x;
        }
        return moves;
    }
};
```
