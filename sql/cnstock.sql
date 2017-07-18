-- ----------------------------
-- Table structure for brief
-- ----------------------------
DROP TABLE IF EXISTS brief;
CREATE TABLE brief ( 
"机构ID" TEXT NOT NULL,
"公司全称" TEXT,
"英文名称" TEXT,
"注册地址" TEXT,
"公司简称" TEXT,
"法定代表人" TEXT,
"公司董秘" TEXT,
"注册资本(万元)" REAL,
"行业种类" TEXT,
"邮政编码" TEXT,
"公司电话" TEXT,
"公司传真" TEXT,
"公司网址" TEXT,
"上市时间" TEXT,
"招股时间" TEXT,
"发行数量（万股）" REAL,
"发行价格（元）" REAL,
"发行市盈率（倍）" REAL,
"发行方式" TEXT,
"主承销商" TEXT,
"上市推荐人" TEXT,
"保荐机构" TEXT,
PRIMARY KEY ("机构ID")
);

DROP TABLE IF EXISTS brief2;
CREATE TABLE brief2 ( 
"机构ID" TEXT NOT NULL,
"公司名称" TEXT,
"公司英文名称" TEXT,
"上市市场" TEXT,
"上市日期" TEXT,
"发行价格" TEXT,
"主承销商" TEXT,
"成立日期" TEXT,
"注册资本" TEXT,
"机构类型" TEXT,
"组织形式" TEXT,
"董事会秘书" TEXT,
"公司电话" TEXT,
"董秘电话" TEXT,
"公司传真" TEXT,
"董秘传真" TEXT,
"公司电子邮箱" TEXT,
"董秘电子邮箱" TEXT,
"公司网址" TEXT,
"邮政编码" TEXT,
"信息披露网址" TEXT,
"证券简称更名历史" TEXT,
"注册地址" TEXT,
"办公地址" TEXT,
"公司简介" TEXT,
"经营范围" TEXT,
PRIMARY KEY ("机构ID")
);

-- ----------------------------
-- Table structure for fzb
-- ----------------------------
DROP TABLE IF EXISTS fzb;
CREATE TABLE fzb (
"机构ID"  TEXT NOT NULL,
"机构名称"  TEXT,
"公告日期"  TEXT,
"截止日期"  TEXT,
"报告年度"  TEXT NOT NULL,
"合并类型"  TEXT,
"报表来源"  TEXT,
"货币资金（元）"  REAL,
"以公允价值计量且其变动计入当期损益的金融资产"  REAL,
"应收票据"  REAL,
"应收账款"  REAL,
"预付款项"  REAL,
"其他应收款"  REAL,
"应收关联公司款"  REAL,
"应收利息"  REAL,
"应收股利"  REAL,
"存货"  REAL,
"其中：消耗性生物资产"  REAL,
"一年内到期的非流动资产"  REAL,
"其他流动资产"  REAL,
"流动资产合计"  REAL,
"可供出售金融资产"  REAL,
"持有至到期投资"  REAL,
"长期应收款"  REAL,
"长期股权投资"  REAL,
"投资性房地产"  REAL,
"固定资产"  REAL,
"在建工程"  REAL,
"工程物资"  REAL,
"固定资产清理"  REAL,
"生产性生物资产"  REAL,
"油气资产"  REAL,
"无形资产"  REAL,
"开发支出"  REAL,
"商誉"  REAL,
"长期待摊费用"  REAL,
"递延所得税资产"  REAL,
"其他非流动资产"  REAL,
"非流动资产合计"  REAL,
"资产总计"  REAL,
"短期借款"  REAL,
"以公允价值计量且其变动计入当期损益的金融负债"  REAL,
"应付票据"  REAL,
"应付账款"  REAL,
"预收款项"  REAL,
"应付职工薪酬"  REAL,
"应交税费"  REAL,
"应付利息"  REAL,
"应付股利"  REAL,
"其他应付款"  REAL,
"应付关联公司款"  REAL,
"一年内到期的非流动负债"  REAL,
"其他流动负债"  REAL,
"流动负债合计"  REAL,
"长期借款"  REAL,
"应付债券"  REAL,
"长期应付款"  REAL,
"专项应付款"  REAL,
"预计负债"  REAL,
"递延所得税负债"  REAL,
"其他非流动负债"  REAL,
"非流动负债合计"  REAL,
"负债合计"  REAL,
"实收资本（或股本）"  REAL,
"资本公积"  REAL,
"盈余公积"  REAL,
"专项储备"  REAL,
"减：库存股"  REAL,
"一般风险准备"  REAL,
"未分配利润"  REAL,
"归属于母公司所有者权益"  REAL,
"少数股东权益"  REAL,
"外币报表折算价差"  REAL,
"非正常经营项目收益调整"  REAL,
"所有者权益（或股东权益）合计"  REAL,
"负债和所有者（或股东权益）合计"  REAL,
"其他综合收益"  REAL,
"递延收益-非流动负债"  REAL,
"结算备付金"  REAL,
"拆出资金"  REAL,
"发放贷款及垫款-流动资产"  REAL,
"衍生金融资产"  REAL,
"应收保费"  REAL,
"应收分保账款"  REAL,
"应收分保合同准备金"  REAL,
"买入返售金融资产"  REAL,
"划分为持有待售的资产"  REAL,
"发放贷款及垫款-非流动资产"  REAL,
"向中央银行借款"  REAL,
"吸收存款及同业存放"  REAL,
"拆入资金"  REAL,
"衍生金融负债"  REAL,
"卖出回购金融资产款"  REAL,
"应付手续费及佣金"  REAL,
"应付分保账款"  REAL,
"保险合同准备金"  REAL,
"代理买卖证券款"  REAL,
"代理承销证券款"  REAL,
"划分为持有待售的负债"  REAL,
"预计负债-流动负债"  REAL,
"递延收益-流动负债"  REAL,
"其中：优先股-非流动负债"  REAL,
"永续债-非流动负债"  REAL,
"长期应付职工薪酬"  REAL,
"其他权益工具"  REAL,
"其中：优先股-所有者权益"  REAL,
"永续债-所有者权益"  REAL,
PRIMARY KEY ("机构ID", "报告年度")
);

-- ----------------------------
-- Table structure for llb
-- ----------------------------
DROP TABLE IF EXISTS llb;
CREATE TABLE llb (
"机构ID"  TEXT NOT NULL,
"机构名称"  TEXT,
"公告日期"  TEXT,
"开始日期"  TEXT,
"截止日期"  TEXT,
"报告年度"  TEXT NOT NULL,
"合并类型"  TEXT,
"报表来源"  TEXT,
"销售商品、提供劳务收到的现金（元）"  REAL,
"收到的税费返还"  REAL,
"收到其他与经营活动有关的现金"  REAL,
"经营活动现金流入小计"  REAL,
"购买商品、接受劳务支付的现金"  REAL,
"支付给职工以及为职工支付的现金"  REAL,
"支付的各项税费"  REAL,
"支付其他与经营活动有关的现金"  REAL,
"经营活动现金流出小计"  REAL,
"经营活动产生的现金流量净额"  REAL,
"收回投资收到的现金"  REAL,
"取得投资收益收到的现金"  REAL,
"处置固定资产、无形资产和其他长期资产收回的现金净额"  REAL,
"处置子公司及其他营业单位收到的现金净额"  REAL,
"收到其他与投资活动有关的现金"  REAL,
"投资活动现金流入小计"  REAL,
"购建固定资产、无形资产和其他长期资产支付的现金"  REAL,
"投资支付的现金"  REAL,
"质押贷款净增加额"  REAL,
"取得子公司及其他营业单位支付的现金净额"  REAL,
"支付其他与投资活动有关的现金"  REAL,
"投资活动现金流出小计"  REAL,
"投资活动产生的现金流量净额"  REAL,
"吸收投资收到的现金"  REAL,
"取得借款收到的现金"  REAL,
"发行债券收到的现金"  REAL,
"收到其他与筹资活动有关的现金"  REAL,
"筹资活动现金流入小计"  REAL,
"偿还债务支付的现金"  REAL,
"分配股利、利润或偿付利息支付的现金"  REAL,
"支付其他与筹资活动有关的现金"  REAL,
"筹资活动现金流出小计"  REAL,
"筹资活动产生的现金流量净额"  REAL,
"四、汇率变动对现金的影响"  REAL,
"四(2)、其他原因对现金的影响"  REAL,
"五、现金及现金等价物净增加额"  REAL,
"期初现金及现金等价物余额"  REAL,
"期末现金及现金等价物余额"  REAL,
"附注："  REAL,
"1、将净利润调节为经营活动现金流量："  REAL,
"净利润"  REAL,
"加：资产减值准备"  REAL,
"固定资产折旧、油气资产折耗、生产性生物资产折旧"  REAL,
"无形资产摊销"  REAL,
"长期待摊费用摊销"  REAL,
"处置固定资产、无形资产和其他长期资产的损失"  REAL,
"固定资产报废损失"  REAL,
"公允价值变动损失"  REAL,
"财务费用"  REAL,
"投资损失"  REAL,
"递延所得税资产减少"  REAL,
"递延所得税负债增加"  REAL,
"存货的减少"  REAL,
"经营性应收项目的减少"  REAL,
"经营性应付项目的增加"  REAL,
"其他"  REAL,
"经营活动产生的现金流量净额2"  REAL,
"2、不涉及现金收支的重大投资和筹资活动："  REAL,
"债务转为资本"  REAL,
"一年内到期的可转换公司债券"  REAL,
"融资租入固定资产"  REAL,
"3、现金及现金等价物净变动情况："  REAL,
"现金的期末余额"  REAL,
"减：现金的期初余额"  REAL,
"加：现金等价物的期末余额"  REAL,
"减：现金等价物的期初余额"  REAL,
"加：其他原因对现金的影响2"  REAL,
"现金及现金等价物净增加额2"  REAL,
"客户存款和同业存放款项净增加额"  REAL,
"向中央银行借款净增加额"  REAL,
"向其他金融机构拆入资金净增加额"  REAL,
"收到原保险合同保费取得的现金"  REAL,
"收到再保险业务现金净额"  REAL,
"保户储金及投资款净增加额"  REAL,
"处置以公允价值计量且其变动计入当期损益的金融资产净增加额"  REAL,
"收取利息、手续费及佣金的现金"  REAL,
"拆入资金净增加额"  REAL,
"回购业务资金净增加额"  REAL,
"客户贷款及垫款净增加额"  REAL,
"存放中央银行和同业款项净增加额"  REAL,
"支付原保险合同赔付款项的现金"  REAL,
"支付利息、手续费及佣金的现金"  REAL,
"支付保单红利的现金"  REAL,
"其中：子公司吸收少数股东投资收到的现金"  REAL,
"其中：子公司支付给少数股东的股利、利润"  REAL,
"投资性房地产的折旧及摊销"  REAL,
PRIMARY KEY ("机构ID", "报告年度")
);

-- ----------------------------
-- Table structure for lrb
-- ----------------------------
DROP TABLE IF EXISTS lrb;
CREATE TABLE lrb (
"机构ID"  TEXT NOT NULL,
"机构名称"  TEXT,
"公告日期"  TEXT,
"开始日期"  TEXT,
"截止日期"  TEXT,
"报告年度"  TEXT NOT NULL,
"合并类型"  TEXT,
"报表来源"  TEXT,
"一、营业总收入"  REAL,
"其中：营业收入（元）"  REAL,
"二、营业总成本"  REAL,
"其中：营业成本"  REAL,
"营业税金及附加"  REAL,
"销售费用"  REAL,
"管理费用"  REAL,
"堪探费用"  REAL,
"财务费用"  REAL,
"资产减值损失"  REAL,
"加：公允价值变动净收益"  REAL,
"投资收益"  REAL,
"其中：对联营企业和合营企业的投资收益"  REAL,
"汇兑收益"  REAL,
"影响营业利润的其他科目"  REAL,
"三、营业利润"  REAL,
"加：补贴收入"  REAL,
"营业外收入"  REAL,
"减：营业外支出"  REAL,
"其中：非流动资产处置损失"  REAL,
"加：影响利润总额的其他科目"  REAL,
"四、利润总额"  REAL,
"减：所得税"  REAL,
"加：影响净利润的其他科目"  REAL,
"五、净利润"  REAL,
"归属于母公司所有者的净利润"  REAL,
"少数股东损益"  REAL,
"六、每股收益："  REAL,
"（一）基本每股收益"  REAL,
"（二）稀释每股收益"  REAL,
"七、其他综合收益"  REAL,
"八、综合收益总额"  REAL,
"其中：归属于母公司"  REAL,
"其中：归属于少数股东"  REAL,
"利息收入"  REAL,
"已赚保费"  REAL,
"手续费及佣金收入"  REAL,
"利息支出"  REAL,
"手续费及佣金支出"  REAL,
"退保金"  REAL,
"赔付支出净额"  REAL,
"提取保险合同准备金净额"  REAL,
"保单红利支出"  REAL,
"分保费用"  REAL,
"其中：非流动资产处置利得"  REAL,
PRIMARY KEY ("机构ID", "报告年度")
);

-- ----------------------------
-- Table structure for holder
-- ----------------------------
DROP TABLE IF EXISTS holder;
CREATE TABLE holder (
holderID  TEXT PRIMARY KEY ,
"股东类型" TEXT NOT NULL,
"机构ID"  TEXT NOT NULL,
"截至日期" TEXT NOT NULL,
"公告日期" TEXT,
CONSTRAINT UX_HOLDER UNIQUE ("股东类型", "机构ID", "截至日期")
);

DROP TABLE IF EXISTS holder_list;
CREATE TABLE holder_list (
holderID  TEXT NOT NULL,
"编号" INT NOT NULL, 
"股东名称" TEXT, 
"持股数量(股)" REAL, 
"持股比例(%)" REAL, 
"股本性质" TEXT,
PRIMARY KEY (holderID, "编号")
);

-- ----------------------------
-- Table structure for sharebonus
-- ----------------------------
DROP TABLE IF EXISTS sharebonus_1;
CREATE TABLE sharebonus_1 (
"机构ID"  TEXT NOT NULL,
"公告日期"  TEXT NOT NULL,
"送股(每10股)" REAL, 
"转增(每10股)" REAL, 
"派息(税前)(每10股)(元)" REAL, 
"进度" TEXT, 
"除权除息日" TEXT,
"股权登记日" TEXT,
"红股上市日" TEXT,
PRIMARY KEY ("机构ID", "公告日期")
);

DROP TABLE IF EXISTS sharebonus_2;
CREATE TABLE sharebonus_2 (
"机构ID"  TEXT NOT NULL,
"公告日期"  TEXT NOT NULL,
"配股方案(每10股配股股数)" REAL, 
"配股价格(元)" REAL, 
"基准股本(万股)" REAL, 
"除权日" TEXT, 
"股权登记日" TEXT,
"缴款起始日" TEXT,
"缴款终止日" TEXT,
"配股上市日" TEXT,
"募集资金合计(元)" REAL,
PRIMARY KEY ("机构ID", "公告日期")
);

-- ----------------------------
-- Table structure for lift_ban
-- ----------------------------
DROP TABLE IF EXISTS lift_ban;
CREATE TABLE lift_ban (
"机构ID" TEXT,
"股东名称" TEXT,
"解禁日期" TEXT,
"新增股份（万）" REAL,
"限售股类型" TEXT,
"是否锁定" INT,
"其他承诺描述" TEXT,
PRIMARY KEY ("机构ID","股东名称","解禁日期")
);

-- ----------------------------
-- Table structure for manager
-- ----------------------------
DROP TABLE IF EXISTS manager;
CREATE TABLE manager ( 
"机构ID" TEXT NOT NULL,
"姓名" TEXT, 
"类型" TEXT,
"职务" TEXT, 
"起始日期" TEXT, 
"终止日期" TEXT,
"薪资" REAL,
PRIMARY KEY ("机构ID","姓名","职务","起始日期")
);

DROP TABLE IF EXISTS person;
CREATE TABLE person ( 
"机构ID" TEXT NOT NULL,
"姓名" TEXT, 
"性别" TEXT,
"出生日期" TEXT,
"学历" TEXT,
"国籍" TEXT,
"简历" TEXT,
PRIMARY KEY ("机构ID","姓名")
);

DROP TABLE IF EXISTS personstock;
CREATE TABLE personstock ( 
"机构ID" TEXT NOT NULL,
"姓名" TEXT, 
"持股数量" INT,
"持股变动原因" TEXT,
"截止日期" TEXT,
PRIMARY KEY ("机构ID","姓名","截止日期")
);

