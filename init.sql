CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- для gen_random_uuid()

CREATE TABLE boards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    total_length_mm REAL,
    defects_summary JSONB,
    quality VARCHAR(10),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE defects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    defect_type TEXT NOT NULL,
    confidence REAL,
    position_from_start_mm REAL,
    width_mm REAL,
    bbox_px JSONB,
    frame_idx INTEGER,
    timestamp TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_defects_board_id ON defects(board_id);

CREATE TABLE cut_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES boards(id) ON DELETE CASCADE UNIQUE,
    segments JSONB,
    total_revenue REAL,
    algorithm TEXT DEFAULT 'greedy',
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_cut_plans_board_id ON cut_plans(board_id);

CREATE TABLE price_list (
    id SERIAL PRIMARY KEY,
    length_m REAL NOT NULL,
    grade INTEGER NOT NULL,
    price REAL NOT NULL,
    UNIQUE(length_m, grade)
);

INSERT INTO price_list (length_m, grade, price) VALUES
(1.0, 0, 150), (1.0, 1, 133), (1.0, 2, 123), (1.0, 3, 117),
(1.5, 0, 225), (1.5, 1, 200), (1.5, 2, 185), (1.5, 3, 175),
(2.0, 0, 300), (2.0, 1, 267), (2.0, 2, 247), (2.0, 3, 233),
(3.0, 0, 450), (3.0, 1, 400), (3.0, 2, 370), (3.0, 3, 350),
(6.0, 0, 900), (6.0, 1, 800), (6.0, 2, 740), (6.0, 3, 700);