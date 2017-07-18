-- ----------------------------
-- Table structure for hk_ah
-- ----------------------------
DROP TABLE IF EXISTS hk_ah;
CREATE TABLE hk_ah ( 
HCode TEXT NOT NULL,
ACode TEXT NOT NULL,
PRIMARY KEY (HCode)
);

DROP TABLE IF EXISTS hk_brief;
CREATE TABLE hk_brief ( 
Code TEXT NOT NULL,
Name TEXT,
"公司名称" TEXT,
"行业" TEXT,
"董事长" TEXT,
"主要持股人" TEXT,
"公司秘书" TEXT,
"注册地址" TEXT,
"公司地址" TEXT,
"上市日期" TEXT,
"核数师" TEXT,
"法律顾问" TEXT,
"经营范围" TEXT,
"主要往来银行" TEXT,
"网站" TEXT,
"电话" TEXT,
"电子邮箱" TEXT,
"传真" TEXT,
PRIMARY KEY (Code)
);

-- ----------------------------
-- Table structure for hk_fzb
-- ----------------------------
DROP TABLE IF EXISTS hk_fzb;
CREATE TABLE hk_fzb ( 
fd_code TEXT NOT NULL,
fd_name TEXT ,
fd_year TEXT ,
fd_type TEXT ,
reporttype_name TEXT ,
fd_repdate TEXT ,
fd_pubdate TEXT ,
fd_unit TEXT ,
unit_name TEXT ,
fd_currency_id TEXT ,
currency_name TEXT ,
fd_attach_comp_rights REAL ,
fd_bank_loan REAL ,
fd_capital_stock REAL ,
fd_cash_and_bankdeposit REAL ,
fd_collected_funds REAL ,
fd_invisible_assets REAL ,
fd_joint_comp_rights REAL ,
fd_liquid_assets REAL ,
fd_liquid_debts REAL ,
fd_min_stkholder_rights REAL ,
fd_non_liquid_debts REAL ,
fd_non_liquitd_assets REAL ,
fd_none_liquid_bank_loan REAL ,
fd_other_investment REAL ,
fd_pay_funds REAL ,
fd_property_factory_facility REAL ,
fd_pure_assets REAL ,
fd_pure_liquid_assets REAL ,
fd_reserves REAL ,
fd_stk_sum REAL ,
fd_stkholder_rights REAL ,
fd_stkup_goods REAL ,
fd_total_assets REAL ,
fd_total_debts REAL ,
PRIMARY KEY (fd_code,fd_year,fd_type)
);

-- ----------------------------
-- Table structure for hk_llb
-- ----------------------------
DROP TABLE IF EXISTS hk_llb;
CREATE TABLE hk_llb ( 
fd_code TEXT NOT NULL,
fd_name TEXT ,
fd_year TEXT ,
fd_type TEXT ,
reporttype_name TEXT ,
fd_repdate TEXT ,
fd_pubdate TEXT ,
fd_unit TEXT ,
unit_name TEXT ,
fd_currency_id TEXT ,
currency_name TEXT ,
fd_bgn_accnt_cash_equival REAL ,
fd_cash_equival_addition REAL ,
fd_end_accnt_cash_equivale REAL ,
fd_fixed_assets_funds REAL ,
fd_foreign_exchng_effect REAL ,
fd_pure_conduct_cash_flowin REAL ,
fd_pure_invest_cash_flowin REAL ,
fd_pure_stock_cash_flowin REAL ,
PRIMARY KEY (fd_code,fd_year,fd_type)
);

-- ----------------------------
-- Table structure for hk_lrb
-- ----------------------------
DROP TABLE IF EXISTS hk_lrb;
CREATE TABLE hk_lrb ( 
fd_code TEXT NOT NULL,
fd_name TEXT ,
fd_year TEXT ,
fd_type TEXT ,
reporttype_name TEXT ,
fd_repdate TEXT ,
fd_pubdate TEXT ,
fd_unit TEXT ,
unit_name TEXT ,
fd_currency_id TEXT ,
currency_name TEXT ,
fd_administration_fee REAL ,
fd_conduct_profit REAL ,
fd_depreciation REAL ,
fd_dividend_base_share REAL ,
fd_gross_profit REAL ,
fd_interest_fee_or_stock_cost REAL ,
fd_min_stkholder_rights REAL ,
fd_profit_after_share REAL ,
fd_profit_after_tax REAL ,
fd_profit_after_tax_divi REAL ,
fd_profit_base_share REAL ,
fd_profit_before_tax REAL ,
fd_sale_bracket_fee REAL ,
fd_sale_cost REAL ,
fd_stkholder_profit REAL ,
fd_stock_dividend REAL ,
fd_tax REAL ,
fd_to_own_joint_comp_profit REAL ,
fd_turnover REAL ,
PRIMARY KEY (fd_code,fd_year,fd_type)
);

-- ----------------------------
-- Table structure for hk_manager
-- ----------------------------
DROP TABLE IF EXISTS hk_manager;
CREATE TABLE hk_manager ( 
Code TEXT NOT NULL,
EName TEXT,
CName TEXT,
Capacity TEXT,
Position TEXT,
BeginDate TEXT,
EndDate TEXT);
