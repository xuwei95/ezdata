/**
 * 英文映射:key = 中文源文案(与源码里的 $t('中文') 对应)。
 * 漏翻则自动回退中文(见 ./index.js 的 fallbackLocale)。逐屏迁移时往对应区块补充即可。
 * 注意:key 一律加引号(含空格/标点/英文的中文文案作 key 必须引号,否则不是合法标识符)。
 */
import backend from './en-backend' // 后端返回消息(res.data.msg)的英文映射
import menu from './en-menu' // 菜单名(route.meta.title)的英文映射
import dataManage from './en-datamanage' // 数据管理模块 UI 文案
import extra from './en-extra' // 其余模块 UI 文案(task/ai/system/monitor/rag/tool 等)

export default {
  ...backend, // 先铺后端报错;下方 UI 文案同名可覆盖
  ...menu, // 菜单名
  ...dataManage, // 数据管理模块
  ...extra, // 其余模块
  // ------- 通用 / common -------
  '保存': 'Save',
  '取消': 'Cancel',
  '确定': 'OK',
  '确认': 'Confirm',
  '删除': 'Delete',
  '新增': 'Add',
  '修改': 'Edit',
  '编辑': 'Edit',
  '查询': 'Search',
  '重置': 'Reset',
  '搜索': 'Search',
  '操作': 'Actions',
  '详情': 'Detail',
  '返回': 'Back',
  '关闭': 'Close',
  '提交': 'Submit',
  '导出': 'Export',
  '导入': 'Import',
  '刷新': 'Refresh',
  '状态': 'Status',
  '备注': 'Remark',
  '创建时间': 'Created',
  '更新时间': 'Updated',
  '操作成功': 'Operation succeeded',
  '操作失败': 'Operation failed',

  // ------- 登录页 / login -------
  '账号': 'Username',
  '密码': 'Password',
  '验证码': 'Captcha',
  '记住密码': 'Remember me',
  '登录': 'Log in',
  '登 录': 'Log in',
  '登 录 中...': 'Logging in...',
  '立即注册': 'Sign up',
  '或': 'or',
  '使用 GitHub 登录': 'Sign in with GitHub',

  // ------- 顶栏 / navbar -------
  '个人中心': 'Profile',
  '布局设置': 'Layout settings',
  '退出登录': 'Log out',
  '正在设置布局大小，请稍候...': 'Applying layout size, please wait...',
  '语言': 'Language',
  '切换语言': 'Switch language',
  '首页': 'Home',

  // ------- 标签页右键菜单 / tagsView -------
  '刷新页面': 'Refresh',
  '关闭当前': 'Close current',
  '关闭其他': 'Close others',
  '关闭左侧': 'Close left',
  '关闭右侧': 'Close right',
  '全部关闭': 'Close all',

  // ------- 错误页 / error pages -------
  '404错误!': '404 Error!',
  '返回首页': 'Back to home',
  '找不到网页！': 'Page not found!',
  '对不起，您正在寻找的页面不存在。尝试检查URL的错误，然后按浏览器上的刷新按钮或尝试在我们的应用程序中找到其他内容。':
    'Sorry, the page you are looking for does not exist. Check the URL for errors, then refresh or try finding something else in the app.',
  '401错误!': '401 Error!',
  '您没有访问权限！': 'You do not have permission!',
  '对不起，您没有访问权限，请不要进行非法操作！您可以返回主页面':
    'Sorry, you do not have permission. Please do not perform any unauthorized actions. You may return to the home page.',
  '回首页': 'Back to home',

  // ------- 注册页 / register -------
  '确认密码': 'Confirm password',
  '注 册': 'Register',
  '注 册 中...': 'Registering...',
  '使用已有账户登录': 'Sign in with an existing account',

  // ------- 接口/请求报错 / request & errorCode -------
  '系统提示': 'Notice',
  '重新登录': 'Re-login',
  '认证失败，无法访问系统资源': 'Authentication failed, cannot access system resources',
  '当前操作没有权限': 'You do not have permission for this operation',
  '访问资源不存在': 'The requested resource does not exist',
  '系统未知错误，请反馈给管理员': 'Unknown system error, please contact the administrator',
  '登录状态已过期，您可以继续留在该页面，或者重新登录': 'Your session has expired. You can stay on this page or log in again',
  '无效的会话，或者会话已过期，请重新登录。': 'Invalid or expired session, please log in again.',
  '后端接口连接异常': 'Failed to connect to the backend API',
  '系统接口请求超时': 'Backend API request timed out',
  '系统接口异常（{code}）': 'Backend API error ({code})',
}
