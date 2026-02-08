const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: process.env.NODE_ENV === 'production' 
    ? '/hhbc-sermon-search/'
    : '/',
  configureWebpack: {
    resolve: {
      fallback: {
        fs: false,
        path: false,
        crypto: false
      }
    }
  },
  chainWebpack: config => {
    config.plugin('html').tap(args => {
      args[0].title = 'HHBC Sermon Search'
      return args
    })
  }
})
