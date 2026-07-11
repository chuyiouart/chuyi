window.WORKSHOP_CONFIG = {
  applicationFormUrl: "./apply.html",
  course: {
    name: "IP 实物化与数字展示五天实战营",
    dates: "2026.10.02-10.06",
    city: "青岛",
    classSize: "10 人最佳，12 人封顶",
  },
  payment: {
    enabled: false,
    approvalRequired: true,
    paymentApiBase: "",
    businessName: "",
    invoiceEntity: "",
    supportText: "付款通道将在初诊通过、名额确认后单独开放。",
    channels: {
      wechat: { enabled: false, label: "微信支付（企业商户）", checkoutUrl: "" },
      alipay: { enabled: false, label: "支付宝（企业商户）", checkoutUrl: "" },
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
