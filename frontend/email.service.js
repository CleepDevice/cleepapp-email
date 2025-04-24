angular
.module("Cleep")
.service("emailService", ["$q", "$rootScope", "rpcService",
function($q, $rootScope, rpcService) {
    const self = this;

    self.setConfig = function(provider, server, port, login, password, tls, ssl, sender) {
        const params = {
            provider,
            login,
            password,
            ...(Boolean(sender) && { sender }),
            ...(Boolean(server) && { server }),
            ...(Boolean(port) && { port }),
            ...(Boolean(tls) && { tls }),
            ...(Boolean(ssl) && { ssl }),
        };
        return rpcService.sendCommand('set_config', 'email', params);
    };

    self.test = function(recipient, provider, server, port, login, password, tls, ssl, sender) {
        const params = {
            recipient,
        };
        return rpcService.sendCommand('test', 'email', params, 30.0);
    };
}]);
