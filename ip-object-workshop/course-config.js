window.WORKSHOP_CONFIG = {
  applicationFormUrl: "https://wj.qq.com/s2/27296919/9499/",
  course: {
    name: "IP 实物化五天实战营",
    dates: "2026.10.02-10.06",
    city: "青岛",
    classSize: "每班限 10 人",
  },
  payment: {
    enabled: false,
    approvalRequired: false,
    paymentApiBase: "",
    businessName: "",
    invoiceEntity: "",
    supportText: "支付系统正在设计，开放后可选择微信、支付宝或银行转账。",
    channels: {
      wechat: { enabled: false, label: "微信支付", checkoutUrl: "" },
      alipay: { enabled: false, label: "支付宝支付", checkoutUrl: "" },
      bank: {
        enabled: false,
        label: "银行对公转账",
        accountName: "",
        bankName: "",
        accountNumber: "",
      },
    },
  },
};
