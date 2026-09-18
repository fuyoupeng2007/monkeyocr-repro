# MonkeyOCR 原版复现：云端部署包

本部署包固定到官方仓库提交：

- commit：`b5e94d3aed972e2e07e7d5c654a0dc588419f4b9`
- 日期：2025-06-13
- 模型：`echo840/MonkeyOCR`（原版3B，不是后续pro-1.2B、pro-3B或v2）
- 默认后端：LMDeploy 0.8.0
- 推荐硬件：单张RTX 3090 24GB或RTX 4090 24GB

选择2025-06-13提交，是因为它仍属于2025-06-05首发的原版MonkeyOCR代码线，同时包含首发后一周内的模型下载、3090共享内存修复和单任务推理修复。实验报告必须写明该提交，而不能写成“完全等同论文作者内部环境”。

## AutoDL实例建议

选择“按量计费”，单卡RTX 3090 24GB；CPU内存至少32GB；数据盘至少50GB，推荐100GB。优先选择带PyTorch 2.5.1、Python 3.10和CUDA 12.4的基础镜像。没有完全相同的镜像也可使用CUDA 12.4开发镜像，脚本会创建独立conda环境。

## 上传后执行

```bash
cd /root/autodl-tmp/monkeyocr-repro
bash scripts/01_install.sh
```

安装脚本会创建`monkeyocr` conda环境、安装官方依赖、下载原版权重、应用官方3090/4090补丁，并执行环境检查。模型下载默认走ModelScope，更适合中国大陆服务器。

安装完成后，以一张图片或一个不超过5页的PDF进行测试：

```bash
conda activate monkeyocr
bash scripts/02_smoke_test.sh /root/autodl-tmp/input/test.pdf
```

输出写入`outputs/smoke_test/`。确认生成Markdown、布局PDF和中间JSON后，再扩大样本规模。

## 计费提醒

GPU实例从开机开始计费。安装和下载期间也计费；完成操作后应在AutoDL控制台关机。关机后GPU停止计费，但付费扩容数据盘可能继续计费。重要结果要同步回本地。

