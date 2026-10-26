class Solution {
public:
    int countIslands(vector<vector<int>>& grid, int k) {
        int m = grid.size();
        int n = grid[0].size();
        int ans = 0;

        int dr[] = {-1, 1, 0, 0};
        int dc[] = {0, 0, -1, 1};

        for (int i = 0; i < m; ++i) {
            for (int j = 0; j < n; ++j) {
                if (grid[i][j] > 0) {
                    long long total_val = 0;
                    vector<pair<int, int>> q;
                    q.push_back({i, j});
                    total_val += grid[i][j];
                    grid[i][j] = 0;

                    int head = 0;
                    while (head < (int)q.size()) {
                        auto [r, c] = q[head++];
                        for (int d = 0; d < 4; ++d) {
                            int nr = r + dr[d];
                            int nc = c + dc[d];
                            if (nr >= 0 && nr < m && nc >= 0 && nc < n && grid[nr][nc] > 0) {
                                total_val += grid[nr][nc];
                                grid[nr][nc] = 0;
                                q.push_back({nr, nc});
                            }
                        }
                    }

                    if (total_val % k == 0) {
                        ans++;
                    }
                }
            }
        }

        return ans;
    }
};