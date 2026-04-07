-- 添加 target_price 欄位到 watchlists 表
-- 執行時間: 部署後自動執行

ALTER TABLE watchlists 
ADD COLUMN IF NOT EXISTS target_price NUMERIC(12, 4) DEFAULT NULL;

-- 添加註解
COMMENT ON COLUMN watchlists.target_price IS '目標價格，用於到價提醒';
