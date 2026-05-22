# Git版本控制规范

> 本规范适用于KZCQL系统的所有架构文档变更管理。
> 创建时间：2026-05-09

## 一、核心原则

1. **所有架构文档变更必须通过Git版本控制**
2. **生成文件不纳入版本控制**（docx、jpg、png等）
3. **变更必须可回滚、可追溯**

## 二、分支策略

```
main (稳定分支)
  ├─ develop (开发分支)
  │    ├─ feature/xxx (特性分支)
  │    └─ ...
  └─ hotfix/xxx (紧急修复)
```

| 分支 | 用途 | 合并目标 |
|------|------|----------|
| main | 稳定版本，经过验证的架构 | - |
| develop | 整合中的变更 | main |
| feature/* | 特性开发 | develop |
| hotfix/* | 紧急修复 | main + develop |

## 三、变更管理流程

| 阶段 | 操作 | 检查点 |
|------|------|--------|
| 1. 创建分支 | 从develop创建feature分支 | 分支命名规范 |
| 2. 开发 | 在feature分支编辑文件 | 符合现有规范风格 |
| 3. 验证 | 执行审查验证变更 | 输出合理 |
| 4. 提交 | git commit（结构化消息） | 消息格式正确 |
| 5. 合并 | PR到develop分支 | 无冲突 |
| 6. 发布 | PR到main分支 | 稳定运行 |

## 四、提交消息格式

```
[类型] 简短描述

详细说明（可选）

关联：Issue/计划文档
```

类型：feat/fix/docs/refactor/test/chore

## 五、回滚机制

### 5.1 三种回退方式

| 方式 | 操作 | 速度 | 安全性 | 适用场景 |
|------|------|------|--------|----------|
| **① 实验分支（推荐）** | `git checkout -b experiment/xxx` → 实验失败后 `git checkout main && git branch -D experiment/xxx` | 秒级 | **零风险** — main完全不受影响 | 新功能实验、规则更新验证 |
| **② 标签+reset** | 先打标签 `git tag v-stable`，再 `git reset --hard v-stable` | 秒级 | 低风险 — 标签保存了快照 | 需要彻底回退到某个稳定版本 |
| **③ revert** | `git revert HEAD` 产生一个新的反向commit | 秒级 | 最安全 — 保留完整历史 | 已推送到远程的commit需要撤回 |

### 5.2 推荐工作流：实验分支策略

```
当前状态: main (v-stable, 已验证)
    │
    ├─→ git tag v-stable-YYYYMMDD          ← 先打标签锁定当前稳定版
    │
    ├─→ git checkout -b experiment/规则更新  ← 创建实验分支
    │       │
    │       ├─ 更新规则文件
    │       ├─ 实际写作测试
    │       │
    │       ├─ 满意 → git checkout main && git merge experiment/规则更新
    │       │
    │       └─ 不满意 → git checkout main && git branch -D experiment/规则更新
    │                   # 秒级回退，零残留
    │
    └─→ main 始终保持稳定
```

### 5.3 单文件回滚

| 场景 | 操作 |
|------|------|
| 回滚单个文件到某次commit | `git checkout <commit> -- 文件路径` |
| 查看某文件的历史版本 | `git log --oneline -- 文件路径` |
| 回滚最近一次commit的某个文件 | `git checkout HEAD~1 -- 文件路径` |

### 5.4 紧急修复

| 场景 | 操作 |
|------|------|
| 紧急修复 | 创建hotfix分支，修复后合并到main |
| 已推送的commit需要撤回 | 使用 `git revert` 产生反向commit |

## 六、标签管理

### 6.1 标签命名规范

| 标签类型 | 格式 | 示例 |
|----------|------|------|
| 架构评估稳定版 | `v-stable-P{版本号}` | `v-stable-P38.4` |
| 规则更新前快照 | `v-pre-{描述}` | `v-pre-APAG-integration` |
| 里程碑版本 | `v{主版本}.{次版本}` | `v1.0` |

### 6.2 标签操作

```bash
# 创建标签
git tag -a v-stable-P38.4 -m 'P38.4架构评估A-级别，76文件14060行变更已验证'

# 查看标签
git tag -l

# 回退到标签
git reset --hard v-stable-P38.4

# 删除标签（如打错了）
git tag -d v-stable-P38.4
```

## 七、远程仓库推送（P34补丁新增）

### 7.1 推送方式

SOLO沙箱环境不支持交互式Git认证（`terminal prompts disabled`），且会话间会重置`~/.git-credentials`凭据缓存。因此采用 **GitHub Personal Access Token (PAT)** 方式进行推送。

### 7.2 推送流程

```bash
# Step 1：写入凭据（每次新会话首次推送前执行）
echo "https://<用户名>:<PAT>@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Step 2：推送
cd /workspace/KZCQL
git push origin main
```

### 7.3 注意事项

| 事项 | 说明 |
|------|------|
| PAT来源 | 由用户提供，主Agent不自行生成 |
| 凭据持久性 | `~/.git-credentials`在会话间会重置，每次新会话需重新写入 |
| 安全性 | PAT仅写入沙箱临时文件，不会泄露到版本库 |
| 推送失败处理 | 提示用户提供PAT，写入后重试 |

### 7.4 推送检查点

- [ ] 凭据已写入 `~/.git-credentials`
- [ ] `git push` 返回 exit code 0
- [ ] 远程仓库与本地一致（`git log --oneline origin/main..main` 为空）

## 八、.gitignore规则

- 04_工作区/产出归档/*/稿件/*.docx
- 04_工作区/产出归档/*/images/*.jpg
- 04_工作区/产出归档/*/images/*.png
- 04_工作区/架构归档/*.md
- *.tmp, *.bak, *.swp
- .DS_Store, Thumbs.db
- /workspace/STATE.md

## 九、文件命名规范

| 文件类型 | 命名格式 | 示例 |
|----------|----------|------|
| Agent规范 | {代号}_{名称}Agent.md | 架构专家组/A1_D5-1_规则执行映射.md |
| 规则文件 | {类别}{名称}.md | 前置撰写规则.md |
| 架构文档 | {名称}.md | Git版本控制规范.md |
| 计划文档 | {名称}计划.md | A1并行架构升级计划.md |

*最后更新：2026-05-22（多平台适配改造：新增实验分支策略、标签管理、三种回退方式）*
