var CodexPanelController = JSB.defineClass('CodexPanelController : UIViewController', {
  viewDidLoad: function() {
    self.promptValue = '';
    self.view.backgroundColor = UIColor.colorWithWhiteAlpha(0.985, 1);
    self.view.layer.cornerRadius = 12;
    self.view.layer.masksToBounds = false;
    self.view.layer.shadowOffset = {width: 0, height: 3};
    self.view.layer.shadowRadius = 10;
    self.view.layer.shadowOpacity = 0.26;
    self.view.layer.shadowColor = UIColor.blackColor();

    var frame = self.view.bounds;
    var width = frame.width > 0 ? frame.width : 430;

    self.headerView = new UIView({x: 0, y: 0, width: width, height: 62});
    self.headerView.backgroundColor = UIColor.colorWithWhiteAlpha(0.96, 1);
    self.headerView.autoresizingMask = (1 << 1);
    self.view.addSubview(self.headerView);

    self.titleLabel = self.makeLabel('Codex Companion', 16, 8, width - 70, 24, 15, true);
    self.titleLabel.textColor = UIColor.darkGrayColor();
    self.headerView.addSubview(self.titleLabel);

    self.subtitleLabel = self.makeLabel('论文对话、精读卡片、脑图和标注助手', 16, 33, width - 70, 18, 11, false);
    self.subtitleLabel.textColor = UIColor.grayColor();
    self.headerView.addSubview(self.subtitleLabel);

    self.closeButton = UIButton.buttonWithType(0);
    self.closeButton.frame = {x: width - 44, y: 10, width: 34, height: 34};
    self.closeButton.autoresizingMask = (1 << 0);
    self.closeButton.setTitleForState('x', 0);
    self.closeButton.setTitleColorForState(UIColor.grayColor(), 0);
    self.closeButton.titleLabel.font = UIFont.boldSystemFontOfSize(16);
    self.closeButton.addTargetActionForControlEvents(self, 'closePanel:', 1 << 6);
    self.headerView.addSubview(self.closeButton);

    self.promptTitleLabel = self.makeLabel('当前输入', 16, 74, width - 32, 18, 12, true);
    self.promptTitleLabel.textColor = UIColor.darkGrayColor();
    self.view.addSubview(self.promptTitleLabel);

    self.promptBox = self.makeBox(14, 96, width - 28, 78);
    self.view.addSubview(self.promptBox);
    self.promptLabel = self.makeLabel('选中论文原文后这里会显示文本；也可以直接点“完整精读”。', 12, 8, width - 52, 58, 12, false);
    self.promptLabel.numberOfLines = 3;
    self.promptLabel.textColor = UIColor.darkGrayColor();
    self.promptBox.addSubview(self.promptLabel);

    self.replyTitleLabel = self.makeLabel('执行结果', 16, 186, width - 32, 18, 12, true);
    self.replyTitleLabel.textColor = UIColor.darkGrayColor();
    self.view.addSubview(self.replyTitleLabel);

    self.replyBox = self.makeBox(14, 208, width - 28, 170);
    self.view.addSubview(self.replyBox);
    self.replyLabel = self.makeLabel('卡片与脑图会写入当前 MarginNote 笔记本。', 12, 8, width - 52, 150, 12, false);
    self.replyLabel.numberOfLines = 8;
    self.replyLabel.textColor = UIColor.darkGrayColor();
    self.replyBox.addSubview(self.replyLabel);

    var buttonW = Math.floor((width - 44) / 2);
    var leftX = 14;
    var rightX = leftX + buttonW + 16;
    self.chatButton = self.makeButton('问 Codex', leftX, 394, buttonW, 'runChat:', true);
    self.fullButton = self.makeButton('完整精读', rightX, 394, buttonW, 'runFullReading:', true);
    self.cardButton = self.makeButton('生成卡片', leftX, 434, buttonW, 'runCard:', false);
    self.mapButton = self.makeButton('生成脑图', rightX, 434, buttonW, 'runMindmap:', false);
    self.hlButton = self.makeButton('同步高亮', leftX, 474, buttonW, 'runHighlights:', false);
    self.healthButton = self.makeButton('检查连接', rightX, 474, buttonW, 'runHealth:', false);

    self.statusLabel = self.makeLabel('本地 Companion：127.0.0.1:48761', 14, 522, width - 28, 28, 11, false);
    self.statusLabel.textColor = UIColor.grayColor();
    self.statusLabel.numberOfLines = 2;
    self.statusLabel.autoresizingMask = (1 << 1 | 1 << 4);
    self.view.addSubview(self.statusLabel);
    self.postPanelEvent('panelBuildStage', {stage: 'stable-controls'});
  },

  closePanel: function(sender) {
    if (self.addon && self.addon.hidePanel) self.addon.hidePanel();
  },

  runChat: function(sender) {
    if (self.addon && self.addon.sendPanelAction) self.addon.sendPanelAction('chat', self.promptText());
  },

  runFullReading: function(sender) {
    if (self.addon && self.addon.sendPanelAction) self.addon.sendPanelAction('generate_full_reading', self.promptText());
  },

  runCard: function(sender) {
    if (self.addon && self.addon.sendPanelAction) self.addon.sendPanelAction('generate_card', self.promptText());
  },

  runMindmap: function(sender) {
    if (self.addon && self.addon.sendPanelAction) self.addon.sendPanelAction('generate_mindmap', self.promptText());
  },

  runHighlights: function(sender) {
    if (self.addon && self.addon.sendPanelAction) self.addon.sendPanelAction('repair_knows_highlights', self.promptText());
  },

  runHealth: function(sender) {
    if (self.addon && self.addon.sendPanelAction) self.addon.sendPanelAction('health', self.promptText());
  }
});

CodexPanelController.prototype.makeBox = function(x, y, width, height) {
  var box = new UIView({x: x, y: y, width: width, height: height});
  box.backgroundColor = UIColor.colorWithWhiteAlpha(0.97, 1);
  box.layer.borderWidth = 0.5;
  box.layer.borderColor = UIColor.lightGrayColor().colorWithAlphaComponent(0.35);
  box.layer.cornerRadius = 8;
  box.layer.masksToBounds = true;
  box.autoresizingMask = (1 << 1);
  return box;
};

CodexPanelController.prototype.makeLabel = function(text, x, y, width, height, size, bold) {
  var label = new UILabel({x: x, y: y, width: width, height: height});
  label.text = text || '';
  label.font = bold ? UIFont.boldSystemFontOfSize(size) : UIFont.systemFontOfSize(size);
  label.autoresizingMask = (1 << 1);
  return label;
};

CodexPanelController.prototype.makeButton = function(title, x, y, width, selector, filled) {
  var button = UIButton.buttonWithType(0);
  button.frame = {x: x, y: y, width: width, height: 32};
  button.setTitleForState(title, 0);
  button.layer.cornerRadius = 8;
  button.layer.masksToBounds = true;
  button.layer.borderWidth = filled ? 0 : 0.5;
  button.layer.borderColor = UIColor.lightGrayColor().colorWithAlphaComponent(0.55);
  button.backgroundColor = filled ? Application.sharedInstance().defaultTintColor : UIColor.colorWithWhiteAlpha(0.995, 1);
  button.setTitleColorForState(filled ? UIColor.whiteColor() : Application.sharedInstance().defaultTintColor, 0);
  button.titleLabel.font = UIFont.boldSystemFontOfSize(12);
  button.addTargetActionForControlEvents(this, selector, 1 << 6);
  this.view.addSubview(button);
  return button;
};

CodexPanelController.prototype.postPanelEvent = function(name, extra) {
  try {
    if (this.addon && this.addon.postEvent) this.addon.postEvent(name, extra || {});
  } catch (err) {}
};

CodexPanelController.prototype.promptText = function() {
  return this.promptValue ? String(this.promptValue) : '';
};

CodexPanelController.prototype.setPromptText = function(text) {
  this.promptValue = text ? String(text) : '';
  if (this.promptLabel) {
    var show = this.promptValue || '选中论文原文后这里会显示文本；也可以直接点“完整精读”。';
    this.promptLabel.text = show.length > 180 ? show.substring(0, 180) + '...' : show;
  }
};

CodexPanelController.prototype.setStatus = function(text) {
  if (!this.statusLabel) return;
  this.statusLabel.text = text ? String(text) : '';
};

CodexPanelController.prototype.setReply = function(text) {
  if (!this.replyLabel) return;
  var show = text ? String(text) : '';
  this.replyLabel.text = show.length > 700 ? show.substring(0, 700) + '...' : show;
};
