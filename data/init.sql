-- Create tables for HDB resale data

-- Resale flat prices table
CREATE TABLE IF NOT EXISTS resale_prices (
    id SERIAL PRIMARY KEY,
    month DATE,
    town VARCHAR(50),
    flat_type VARCHAR(20),
    block VARCHAR(10),
    street_name VARCHAR(100),
    storey_range VARCHAR(10),
    floor_area_sqm NUMERIC(8, 2),
    flat_model VARCHAR(50),
    lease_commence_date INTEGER,
    resale_price NUMERIC(10, 2),
    remaining_lease_years NUMERIC(5, 2)
);

-- HDB completion status table
CREATE TABLE IF NOT EXISTS completion_status (
    id SERIAL PRIMARY KEY,
    financial_year INTEGER,
    town_or_estate VARCHAR(50),
    status VARCHAR(50),
    no_of_units INTEGER
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_resale_month ON resale_prices(month);
CREATE INDEX IF NOT EXISTS idx_resale_town ON resale_prices(town);
CREATE INDEX IF NOT EXISTS idx_resale_flat_type ON resale_prices(flat_type);
CREATE INDEX IF NOT EXISTS idx_completion_year ON completion_status(financial_year);
CREATE INDEX IF NOT EXISTS idx_completion_town ON completion_status(town_or_estate); 