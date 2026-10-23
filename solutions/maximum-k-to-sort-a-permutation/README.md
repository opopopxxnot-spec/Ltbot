# Maximum K to Sort a Permutation (Medium)

- **Problem URL:** https://leetcode.com/problems/maximum-k-to-sort-a-permutation/
- **Language:** CPP
- **Runtime:** 1 ms (Beats 54.3%)
- **Date:** 2026-10-23 05:09:01 UTC

```cpp
class Solution {
public:
    int sortPermutation(vector<int>& nums) {
        int ans = -1;
        for (int i = 0; i < nums.size(); ++i) {
            if (nums[i] != i) {
                if (ans == -1) {
                    ans = nums[i];
                } else {
                    ans &= nums[i];
                }
            }
        }
        return ans == -1 ? 0 : ans;
    }
};
```
