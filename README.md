# buaa_keep_login

# 功能简介

基于某个命令行下登录buaa网关改写的保持登录python脚本。通过简单粗暴的ping大型网站的方式判断是否与公网保持连接，如果与公网无连接，则重新登陆网关。

其实除了ping大网站之外，访问网关获取连接状态是更优雅的判断网关是否处于登录状态的方法。但这种方法存在一个问题，当开启了clash的全局代理，会导致对网关的访问也被转发到代理服务器上，导致无法查询在线状态。在这种情况下，不优雅的ping方法反而更有效。

代码中设置了时间间隔，并设置了多个可以ping的网站，只有在所有网站都ping不到的时候，才会重新发起连接，避免频繁ping操作与网关连接等操作产生不良影响。

# 针对clash开启全局代理时无法访问网关进行重连的处理

开启clash全局代理会导致断网也无法访问网关，此时会进入到只有【关闭代理才能连接网关->连接网关才能关闭代理】的怪圈，因此代码中通过clash的RESTful API来对clash的代理模式进行操作，当该功能开启时，检测到网络连接中断重连网络时，会先将clash切换到DIRECT直连模式，再连接网关。该功能默认关闭，需要在代码中手动开启。

开启方式：

将

if_close_clash_proxy=False

改为

if_close_clash_proxy=True

并修改port与secret为电脑中clash内的值。

默认情况下secret信息与port信息在 C:\Users\[YOUR_USERNAME]\.config\clash\config.yaml中，可自行复制，当然也可自行修改。

使用该功能请务必将clash的Random Controller Port关闭。该选项位于clash的设置->general->Random Controller Port
