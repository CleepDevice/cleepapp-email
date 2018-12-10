/**
 * Smtp config directive
 * Handle smtp configuration
 */
var smtpConfigDirective = function(toast, smtpService, raspiotService) {

    var smtpController = ['$scope', function($scope)
    {
        var self = this;
        self.providers = [];
        self.provider = null;
        self.server = '';
        self.port = '';
        self.login = '';
        self.password = '';
        self.tls = false;
        self.ssl = false;
        self.sender = '';
        self.recipient = '';

        /**
         * Load values from specified config
         */
        self.__loadFromConfig = function(config)
        {
            self.providers = config.providers;
            for(var i=0; i<self.providers.length; i++) {
                console.log(''+config.provider+'=='+self.providers[i].key);
                if(config.provider==self.providers[i].key) {
                    self.provider = self.providers[i];
                    break;
                }
            }
            self.server = config.server;
            self.port = config.port;
            self.login = config.login;
            self.password = config.password;
            self.tls = config.tls;
            self.ssl = config.ssl;
            self.sender = config.sender;
        };

        /**
         * Set config
         */
        self.setConfig = function()
        {
            smtpService.setConfig(self.provider.key, self.server, self.port, self.login, self.password, self.tls, self.ssl, self.sender)
                .then(function(resp) {
                    return raspiotService.reloadModuleConfig('smtp');
                })
                .then(function(config) {
                    self.__loadFromConfig(config);
                    toast.success('Configuration saved.');
                });
        };

        /**
         * Test
         */
        self.test = function()
        {
            toast.loading('Sending test email...');
            smtpService.test(self.recipient, self.provider.key, self.server, self.port, self.login, self.password, self.tls, self.ssl, self.sender)
                .then(function(resp) {
                    toast.success('Email sent successfully. Check your mailbox.');
                });
        };

        /**
         * Init controller
         */
        self.init = function()
        {
            raspiotService.getModuleConfig('smtp')
                .then(function(config) {
                    for( var i=0; i<self.providers.length; i++ )
                    {
                        if( config.smtp_server===self.providers[i].smtp )
                        {
                            self.provider = self.providers[i].key;
                            break;
                        }
                    }
                    self.__loadFromConfig(config);
                });
        };

        $scope.$watch(function() {
            return self.provider
        }, function(newVal, oldVal) {
            if(newVal && oldVal && newVal.key!=oldVal.key) {
                console.log(newVal, oldVal);
                //erase inputs
                self.server = '';
                self.port = '';
                self.login = '';
                self.password = '';
                self.tls = '';
                self.ssl = '';
                self.sender = '';
            }
        });

    }];

    var smtpLink = function(scope, element, attrs, controller) {
        controller.init();
    };

    return {
        templateUrl: 'smtp.config.html',
        scope: true,
        controller: smtpController,
        controllerAs: 'smtpCtl',
        link: smtpLink
    };
};

var RaspIot = angular.module('RaspIot');
RaspIot.directive('smtpConfigDirective', ['toastService', 'smtpService', 'raspiotService', smtpConfigDirective])

