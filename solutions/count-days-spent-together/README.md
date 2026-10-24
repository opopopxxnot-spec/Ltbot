# Count Days Spent Together (Easy)

- **Problem URL:** https://leetcode.com/problems/count-days-spent-together/
- **Language:** CPP
- **Runtime:** 0 ms (Beats 100%)
- **Date:** 2026-10-24 04:53:10 UTC

```cpp
#include <string>
#include <vector>
#include <numeric>
#include <algorithm>

using namespace std;

class Solution {
public:
    int countDaysTogether(string arriveAlice, string leaveAlice, string arriveBob, string leaveBob) {
        vector<int> days = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
        
        auto toDayOfYear = [&](const string& s) {
            int m = stoi(s.substr(0, 2));
            int d = stoi(s.substr(3, 2));
            int total = d;
            for (int i = 0; i < m - 1; ++i) {
                total += days[i];
            }
            return total;
        };

        int startAlice = toDayOfYear(arriveAlice);
        int endAlice = toDayOfYear(leaveAlice);
        int startBob = toDayOfYear(arriveBob);
        int endBob = toDayOfYear(leaveBob);

        int overlapStart = max(startAlice, startBob);
        int overlapEnd = min(endAlice, endBob);

        return max(0, overlapEnd - overlapStart + 1);
    }
};
```
