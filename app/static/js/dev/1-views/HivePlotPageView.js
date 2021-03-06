var HivePlotPageView = PageView.extend({
	events: {
		"click .timeline-value a": "clickTimelineValue",

		"change #mapNumericalValue": "changeNumericalValue",
		"change #mapAxisScale": "changeAxisScale",
		"blur #mapAxis1": "changeMapAxis1",
		"blur #mapAxis2": "changeMapAxis2",
		"blur #mapAxis3": "changeMapAxis3",
		"change #directionAxis1": "changeDirectionAxis1",
		"change #directionAxis2": "changeDirectionAxis2",
		"change #directionAxis3": "changeDirectionAxis3",
		"click a.apply-filter": "clickApplyFilter",
		"blur #filterProtocols": "changeFilterProtocols",
		"blur #filterPorts": "changeFilterPorts",
		"blur #filterIPs": "changeFilterIPs",
		"change #filterPortsType": "changeFilterPortsType",
		"change #filterProtocolsType": "changeFilterProtocolsType",
		"change #filterIPsType": "changeFilterIPsType",
	},
	initialize: function() {
		this.template = _.template($("#hive-plot-page-template").html());
		this.loaderTemplate = _.template($("#loader-template").html());
		
		var that = this;
		// make function available to unbind later
		this._onResize = function() { that.render(); };
		$(window).bind("resize", this._onResize);
		
		this.nodes = new IndexQuery(null, { index: "nodes" });
		this.flows = new Flows();
		this.timelineModel = new TimelineModel();
		this.hivePlotModel = new HivePlotModel();
		
		this.timelineView = new TimelineView({
			model: this.timelineModel
		});
		this.hivePlotView = new HivePlotView({
			nodes: this.nodes,
			flows: this.flows,
			timeline: this.timelineModel,
			model: this.hivePlotModel
		});

		// bind after initialization of HivePlotView to get event after the HivePlotView instance
		this.nodes.bind("reset", this.updateIfLoaded, this);
		this.flows.bind("reset", this.updateIfLoaded, this);
    	
		this.timelineModel.bind("change:interval", this.changeBucketInterval, this);
		this.timelineModel.bind("change:value", this.changeTimelineValue, this);
		this.hivePlotModel.bind("change:numericalValue", this.numericalValueChanged, this);
		this.hivePlotModel.bind("change:axisScale", this.axisScaleChanged, this);
		this.hivePlotModel.bind("change:mapAxis1", this.mapAxis1Changed, this);
		this.hivePlotModel.bind("change:mapAxis2", this.mapAxis2Changed, this);
		this.hivePlotModel.bind("change:mapAxis3", this.mapAxis3Changed, this);
		this.hivePlotModel.bind("change:directionAxis1", this.directionAxis1Changed, this);
		this.hivePlotModel.bind("change:directionAxis2", this.directionAxis2Changed, this);
		this.hivePlotModel.bind("change:directionAxis3", this.directionAxis3Changed, this);

		// fetch at the end because a cached request calls render immediately!
		this.nodes.fetch();
	},
	remove: function() {
		if(this.timelineView) {
			this.timelineView.remove();
		}
    		if(this.hivePlotView) {
			this.hivePlotView.remove();
		}
    	
		$(window).unbind("resize", this._onResize);
		$(this.el).remove();
		return this;
	},
	render: function() {
		$(this.el).html(this.template());
		
		this.loader = $(this.loaderTemplate());
		$(".content", this.el).append(this.loader);
		
		this.asideScrollApi = $("aside", this.el)
			.jScrollPane()
			.data("jsp");
		
		$("#footbar", this.el).append(this.timelineView.el);
		// rewire events because we removed the view from the dom
		this.timelineView.delegateEvents();
		this.timelineView.render();
    	
		$(".canvas", this.el).append(this.hivePlotView.el);
		// rewire events because we removed the view from the dom
		this.hivePlotView.delegateEvents();
		this.hivePlotView.render();
		
		this.updateIfLoaded();
		
		// form defaults
		$("#mapNumericalValue", this.el).val(this.hivePlotModel.get("numericalValue"));
		$("#mapAxisScale", this.el).val(this.hivePlotModel.get("axisScale"));
		$("#mapAxis1").val(this.hivePlotModel.get("mapAxis1"));
		$("#mapAxis2").val(this.hivePlotModel.get("mapAxis2"));
		$("#mapAxis3").val(this.hivePlotModel.get("mapAxis3"));
		$("#directionAxis1", this.el).val(this.hivePlotModel.get("directionAxis1"));
		$("#directionAxis2", this.el).val(this.hivePlotModel.get("directionAxis2"));
		$("#directionAxis3", this.el).val(this.hivePlotModel.get("directionAxis3"));

		$("#filterPorts", this.el).val(this.hivePlotModel.get("filterPorts"));
		$("#filterPortsType", this.el).val(this.hivePlotModel.get("filterPortsType"));
    		$("#filterIPs", this.el).val(this.hivePlotModel.get("filterIPs"));
		$("#filterIPsType", this.el).val(this.hivePlotModel.get("filterIPsType"));
    		$("#filterProtocols", this.el).val(this.hivePlotModel.get("filterProtocols"));
		$("#filterProtocolsType", this.el).val(this.hivePlotModel.get("filterProtocolsType"));

		$(".timeline-value li[data-value='" + this.timelineModel.get("value") + "']", this.el)
			.addClass("active");
		
		$("aside .help", this.el).popover({ offset: 24 });
		
		return this;
	},
	hide: function() {
		$(window).unbind("resize", this._onResize);
		return PageView.prototype.hide.call(this);
	},
	show: function() {
		$(window).bind("resize", this._onResize);
		return PageView.prototype.show.call(this);
	},
	updateIfLoaded: function() {
		if(!$(this.el).html()) {
			this.render();
		}
		
		this.loader.hide();
		
		return this;
	},
	fetchFlows: function() {
		var interval = this.timelineModel.get("interval");
		var bucket_size = this.timelineModel.get("bucket_size");
	
	
		var data = { 
			"start_bucket": Math.floor(interval[0].getTime() / 1000),
			"end_bucket": Math.floor(interval[1].getTime() / 1000),
			"bucket_size": bucket_size
		};

		aggregate_fields =  FlowInspector.COL_SRC_IP + "," + FlowInspector.COL_DST_IP
		data = FlowInspector.addToFilter(data, this.hivePlotModel, aggregate_fields, true);
		if (data == null) {
			return;
		}

		this.flows.fetch({ data: data });
	},
	changeBucketInterval: function(model, interval) {
		this.loader.show();
		this.fetchFlows();
	},
	changeNumericalValue: function() {
		this.hivePlotModel.set({
			numericalValue: $("#mapNumericalValue", this.el).val()
		});
	},
	numericalValueChanged: function(model, value) {
		$("#mapNumericalValue", this.el).val(value);
	},
	changeAxisScale: function() {
		this.hivePlotModel.set({
			axisScale: $("#mapAxisScale", this.el).val()
		});
	},
	axisScaleChanged: function(model, value) {
		$("#mapAxisScale", this.el).val(value);
	},
	changeMapAxis1: function() {
		this.hivePlotModel.set({
			mapAxis1: $.trim($("#mapAxis1", this.el).val())
		});
	},
	mapAxis1Changed: function(model, value) {
		$("#mapAxis1", this.el).val(value);
	},
	changeMapAxis2: function() {
		this.hivePlotModel.set({
			mapAxis2: $.trim($("#mapAxis2", this.el).val())
		});
	},
	mapAxis2Changed: function(model, value) {
		$("#mapAxis2", this.el).val(value);
	},
	changeMapAxis3: function() {
		this.hivePlotModel.set({
			mapAxis3: $.trim($("#mapAxis3", this.el).val())
		});
	},
	mapAxis3Changed: function(model, value) {
		$("#mapAxis3", this.el).val(value);
	},
	changeDirectionAxis1: function() {
		this.hivePlotModel.set({
			directionAxis1: $("#directionAxis1", this.el).val()
		});
	},
	directionAxis1Changed: function(model, value) {
		$("#directionAxis1", this.el).val(value);
	},
	changeDirectionAxis2: function() {
    		this.hivePlotModel.set({
			directionAxis2: $("#directionAxis2", this.el).val()
		});
	},
	directionAxis2Changed: function(model, value) {
    		$("#directionAxis2", this.el).val(value);
	},
	changeDirectionAxis3: function() {
		this.hivePlotModel.set({
			directionAxis3: $("#directionAxis3", this.el).val()
		});
	},
	directionAxis3Changed: function(model, value) {
		$("#directionAxis3", this.el).val(value);
	},
	changeFilterProtocols : function(model, value) {
		this.hivePlotModel.set({
			filterProtocols: $("#filterProtocols", this.el).val()
		});
	},
	changeFilterPorts : function(model, value) {
		this.hivePlotModel.set({
			filterPorts: $("#filterPorts", this.el).val()
		});
	},
	changeFilterIPs : function(model, value) {
		this.hivePlotModel.set({
			filterIPs: $("#filterIPs", this.el).val()
		});
	},
	changeFilterPortsType : function(model, value) {
		this.hivePlotModel.set({
			filterPortsType: $("#filterPortsType", this.el).val()
		});
	},
	changeFilterProtocolsType : function(model, value) {
		this.hivePlotModel.set({
			filterProtocolsType: $("#filterProtocolsType", this.el).val()
		});
	},
	changeFilterIPsType : function(model, value) {
		this.hivePlotModel.set({
			filterIPsType: $("#filterIPsType", this.el).val()
		});
	},
	clickApplyFilter : function() {
		this.loader.show();
		this.fetchFlows();
	},
	clickTimelineValue: function(e) {
		var target = $(e.target).parent();
		this.timelineModel.set({ value: target.data("value") });
	},
	changeTimelineValue: function(model, value) {
		$(".timeline-value li", this.el).removeClass("active");
		$(".timeline-value li[data-value='" + value + "']", this.el)
			.addClass("active");
	},
});
