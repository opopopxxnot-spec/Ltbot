#include <vector>
#include <numeric>
#include <algorithm>

using namespace std;

class Solution {
public:
    int sortableIntegers(vector<int>& nums) {
        int n = nums.size();
        
        auto check = [&](int k) -> bool {
            int prev_max = -1;
            for (int i = 0; i < n; i += k) {
                int L = i;
                int R = i + k - 1;
                
                int cur_min = nums[L];
                int cur_max = nums[L];
                int drops = 0;
                
                for (int j = L; j < R; ++j) {
                    if (nums[j] > nums[j + 1]) {
                        drops++;
                    }
                    if (nums[j + 1] < cur_min) cur_min = nums[j + 1];
                    if (nums[j + 1] > cur_max) cur_max = nums[j + 1];
                }
                
                if (nums[R] > nums[L]) {
                    drops++;
                }
                
                if (drops > 1) return false;
                if (i > 0 && prev_max > cur_min) return false;
                
                prev_max = cur_max;
            }
            return true;
        };

        vector<int> divisors;
        for (int d = 1; d * d <= n; ++d) {
            if (n % d == 0) {
                divisors.push_back(d);
                if (d * d != n) {
                    divisors.push_back(n / d);
                }
            }
        }

        int ans = 0;
        for (int k : divisors) {
            if (check(k)) {
                ans += k;
            }
        }

        return ans;
    }
};