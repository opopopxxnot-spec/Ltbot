# Two Sum (Easy)

- **Problem URL:** https://leetcode.com/problems/two-sum/
- **Language:** CPP
- **Runtime:** 1 ms (Beats 83.4%)
- **Date:** 2026-11-04 06:52:21 UTC

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
