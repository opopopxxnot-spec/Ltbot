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