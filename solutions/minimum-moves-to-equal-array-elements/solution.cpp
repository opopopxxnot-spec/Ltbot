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