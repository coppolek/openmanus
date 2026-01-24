import argparse
import asyncio

from app.agent.manus import Manus
from app.logger import logger


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Run Manus agent with a prompt")
    parser.add_argument(
        "--prompt", type=str, required=False, help="Input prompt for the agent"
    )
    return parser.parse_args()


def get_user_prompt(args: argparse.Namespace) -> str:
    """获取用户提示输入，优先使用命令行参数，否则交互式获取"""
    if args.prompt:
        return args.prompt
    return input("Enter your prompt: ")


def validate_prompt(prompt: str) -> bool:
    """验证用户提示是否有效"""
    if not prompt.strip():
        logger.warning("Empty prompt provided.")
        return False
    return True


async def run_agent_task(agent: Manus, prompt: str) -> None:
    """执行代理任务"""
    logger.warning("Processing your request...")
    await agent.run(prompt)
    logger.info("Request processing completed.")


async def create_agent() -> Manus:
    """创建并初始化 Manus 代理实例"""
    return await Manus.create()


async def main():
    """主函数：运行 Manus 代理的主入口点"""
    args = parse_arguments()
    agent = await create_agent()

    try:
        prompt = get_user_prompt(args)
        if not validate_prompt(prompt):
            return
        await run_agent_task(agent, prompt)
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
