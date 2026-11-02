# Minimum Moves to Equal Array Elements II (Medium)

- **Problem URL:** https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/
- **Language:** CPP
- **Runtime:** 0 ms (Beats 100%)
- **Date:** 2026-11-02 06:34:49 UTC

```cpp
class Solution {
public:
    int minMoves2(vector<int>& nums) {
        int n = nums.size();
        nth_element(nums.begin(), nums.begin() + n / 2, nums.end());
        int median = nums[n / 2];
        long long moves = 0;
        for (int x : nums) {
            moves += std::abs((long long)x - median);
        }
        return moves;
    }
};
```
