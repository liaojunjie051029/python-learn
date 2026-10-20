from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Default App"
    app_env: str = "dev"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

# BaseSettings：从环境变量和 .env 读取配置；
# APP_NAME：自动对应 app_name；
# DEBUG=true：自动转换成 Python 的 bool；
# @lru_cache：同一个进程中复用同一个配置对象；会让配置对象在当前 Python 进程中只创建一次。生产环境通常也希望配置在服务启动时确定，而不是请求过程中动态变化。会缓存 get_settings() 的返回对象。
# extra="ignore"：忽略 .env 中暂时没有定义的其他变量。