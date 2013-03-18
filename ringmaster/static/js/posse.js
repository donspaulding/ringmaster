window.Posse = (function(other_posse, undefined){
	function Posse(config){
		if (this == document || this == window){
			var self = {};
		}
		else {
			var self = this;			
		}
		
		self._previous_posse = other_posse;

		self.no_conflict = function(name){
			window[name] = self;
			window.Posse = self._previous_posse;
			return self;
		}

		self.format_data = function(data){
			if (JSON && JSON.parse){
				return JSON.parse(data);
			}
			return data;
		}

		self.origin_matches = function(evt){
			for (i in allowed_origins){
				if (evt.origin == allowed_origins[i]){
					return;
				}
			}
			throw "Invalid origin! '" + evt.origin + "' not in " + allowed_origins;
		}

		self.on = function(name, func){
			self.config.handlers[name] = func;
			self.source.addEventListener(name, function(event){
				if (self.verify_origin){
					self.config.origin_checker(event);
				}
				var data = self.config.data_formatter(event.data);
				return func(data);
			}, false);
			return self;
		}

		self.reset_source = function(){
			self.disconnect();
			self.source = new EventSource(self.config.url);
			for (name in self.config.handlers){
				self.on(name, self.config.handlers[name]);
			}
		}

		self.disconnect = function(){
			self.source && self.source.close();
		}

		self.config = {
			url: "/sse/",
			verify_origin: true,
			allowed_origins: [window.location.origin],
			origin_checker: self.origin_matches,
			data_formatter: self.format_data,
			handlers: {}
		};

		self.set = function(name, value){
			if (value != undefined){
				self.config[name] = value;
			} 
			else {
				var config = name;
				for (name in config){
					self.config[name] = config[name];
				}
			}
			self.reset_source();
			return self;
		}

		// Initialize the source with the config.
		self.set(config || {});
	}
	return Posse;
})(window.Posse);