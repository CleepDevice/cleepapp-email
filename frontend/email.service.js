/**
 * Smtp service
 * Handle smtp module requests
 */
var smtpService = function($q, $rootScope, rpcService) {
    var self = this;

   self.setConfig = function(provider, server, port, login, password, tls, ssl, sender) {
        return rpcService.sendCommand('set_config', 'smtp', {'provider':provider, 'server':server, 'port':port, 'login':login, 'password':password, 'tls':tls, 'ssl':ssl, 'sender':sender});
    };

    self.test = function(recipient, provider, server, port, login, password, tls, ssl, sender) {
        return rpcService.sendCommand('test', 'smtp', {'recipient':recipient, 'provider':provider, 'server':server, 'port':port, 'login':login, 'password':password, 'tls':tls, 'ssl':ssl, 'sender':sender}, 60);
    };

};
    
var RaspIot = angular.module('RaspIot');
RaspIot.service('smtpService', ['$q', '$rootScope', 'rpcService', smtpService]);

