# 如何获取 GitHub 个人访问令牌（Personal Access Token）

## 步骤 1：登录 GitHub

打开浏览器，访问 [GitHub](https://github.com/) 并登录你的账户。

## 步骤 2：进入设置页面

点击右上角的头像，然后选择 **Settings**（设置）。

## 步骤 3：进入开发者设置

在左侧菜单中，向下滚动找到 **Developer settings**（开发者设置），点击进入。

## 步骤 4：生成新令牌

在 **Developer settings** 页面中，选择 **Personal access tokens**（个人访问令牌），然后点击 **Generate new token**（生成新令牌）。

## 步骤 5：配置令牌

- **Note**（备注）：为你的令牌添加一个描述性的名称，以便将来识别。
- **Expiration**（过期时间）：选择令牌的有效期。你可以选择 30 天、60 天、90 天或自定义时间，甚至选择不设置过期时间（不推荐）。
- **Select scopes**（选择权限）：根据你的需求选择令牌的权限。对于获取仓库的星标数量，至少需要勾选 `repo` 权限。如果你只需要读取公开仓库的信息，可以勾选 `public_repo` 权限。

## 步骤 6：生成令牌

配置完成后，点击页面底部的 **Generate token** 按钮。

## 步骤 7：保存令牌

生成的令牌会显示在页面上。**务必将令牌复制并保存到安全的地方**，因为你以后将无法再次查看这个令牌。如果丢失了令牌，你需要重新生成一个新的令牌。

## 步骤 8：设置环境变量

将令牌设置为环境变量 `GITHUB_TOKEN`。具体操作取决于你的操作系统：

### Windows

1. 打开命令提示符或 PowerShell。
2. 运行以下命令：
   ```sh
   setx GITHUB_TOKEN "your_personal_access_token"
   ```
3. 关闭并重新打开命令提示符或 PowerShell，以使环境变量生效。

### macOS/Linux

1. 打开终端。
2. 编辑你的 shell 配置文件（例如 `.bashrc`、`.zshrc` 或 `.profile`），添加以下行：
   ```sh
   export GITHUB_TOKEN="your_personal_access_token"
   ```
3. 保存文件并运行以下命令以使更改生效：
   ```sh
   source ~/.bashrc  # 或者 source ~/.zshrc, source ~/.profile，取决于你使用的 shell
   ```

完成以上步骤后，你的 GitHub 个人访问令牌就已经配置好了。你的脚本将能够使用这个令牌来访问 GitHub API 并获取仓库的星标数量。
