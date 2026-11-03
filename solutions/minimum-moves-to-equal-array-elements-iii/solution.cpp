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