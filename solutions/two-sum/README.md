# Two Sum (Easy)

- **Problem URL:** https://leetcode.com/problems/two-sum/
- **Language:** CPP
- **Runtime:** 2 ms (Beats 73.9%)
- **Date:** 2026-11-03 14:45:53 UTC

```cpp
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> mp;
        for (int i = 0; i < nums.size(); i++) {
            if (mp.count(target - nums[i])) return {mp[target - nums[i]], i};
            mp[nums[i]] = i;
        }
        return {};
    }
};
```
