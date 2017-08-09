-- ----------------------------
-- Table structure for brief
-- ----------------------------
DROP TABLE IF EXISTS brief3b;
CREATE TABLE brief3b ( 
"机构ID" TEXT NOT NULL,
"机构名称" TEXT,
"机构简称" TEXT,
"英文全称" TEXT,
"英文简称" TEXT,
"机构类型(大类)" TEXT,
"机构类型(小类)" TEXT,
"是否上市" TEXT,
"法定代表人" TEXT,
"董事长" TEXT,
"总经理" TEXT,
"董事会秘书" TEXT,
"董秘联系电话" TEXT,
"董秘传真" TEXT,
"董秘邮箱" TEXT,
"证券代表" TEXT,
"证券代表电话" TEXT,
"证券代表传真" TEXT,
"证券代表邮箱" TEXT,
"成立日期" TEXT,
"机构状态" TEXT,
"币种" TEXT,
"注册资本(万元)" TEXT,
"职工人数" TEXT,
"公司注册地址" TEXT,
"注册地址邮箱编码" TEXT,
"办公地址" TEXT,
"办公地址邮政编码" TEXT,
"公司电话" TEXT,
"公司传真" TEXT,
"公司电子邮箱" TEXT,
"公司网址" TEXT,
"主办券商" TEXT,
"做市商" TEXT,
"律师事务所" TEXT,
"会计事务所" TEXT,
"转让方式" TEXT,
"证监会行业" TEXT,
"地区" TEXT,
"主营业务" TEXT,
PRIMARY KEY ("机构ID")
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
