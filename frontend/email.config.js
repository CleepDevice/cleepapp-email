angular
.module('Cleep')
.directive('emailConfigComponent', ['toastService', 'emailService', 'cleepService',
function(toast, emailService, cleepService) {

    const emailController = ['$scope', function($scope) {
        const self = this;
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

        self.$onInit = function() {
            cleepService.getModuleConfig('email')
                .then(function(config) {
                    self.__loadFromConfig(config);
                });
        };

        /**
         * Load values from specified config
         */
        self.__loadFromConfig = function(config) {
            const providers = [];
            for (const provider of config.providers) {
                providers.push({
                    label: provider.label,
                    value: provider.key,
                });
                if (config.provider === provider.key) {
                    self.provider = provider.key
                }
            }
            self.providers = providers;
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
        self.setConfig = function() {
            emailService.setConfig(self.provider, self.server, self.port, self.login, self.password, self.tls, self.ssl, self.sender)
                .then(function(resp) {
                    return cleepService.reloadModuleConfig('email');
                })
                .then(function(config) {
                    self.__loadFromConfig(config);
                    toast.success('Configuration saved.');
                });
        };

        /**
         * Test
         */
        self.test = function() {
            toast.loading('Sending test email...');
            emailService.test(self.recipient, self.provider.key, self.server, self.port, self.login, self.password, self.tls, self.ssl, self.sender)
                .then(function(resp) {
                    toast.success('Email sent successfully. Check your mailbox.');
                });
        };

        $scope.$watch(function() {
            return self.provider
        }, function(newVal, oldVal) {
            if (newVal !== oldVal) {
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

    return {
        templateUrl: 'email.config.html',
        replace: true,
        controller: emailController,
        controllerAs: '$ctrl',
    };
}]);
