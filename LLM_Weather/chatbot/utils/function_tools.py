import google.generativeai as genai


class WeatherFunctionTools:
    """Function calling tools for weather chatbot"""
    
    @staticmethod
    def get_weather_tools():
        """Returns weather-related Function calling tools."""
        return [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="get_ultra_short_term_weather",
                        description="Provides ultra-short-term weather forecast information within 1-6 hours. Includes detailed weather information from current weather up to 6 hours ahead.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "location": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Location name where you want to know the weather (e.g., Seoul, Chuncheon, Nowon, Hyoja-dong, etc.). If the user doesn't specify a location or expresses it as 'current location', 'here', 'current', etc., pass an empty string ('')."
                                ),
                                "hours": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="How many hours ahead to check the weather (1-6 hours, default: 1)"
                                ),
                                "full_day": genai.protos.Schema(
                                    type=genai.protos.Type.BOOLEAN,
                                    description="Set to true when user asks for full day weather information (e.g., 'today's weather', 'all day weather', 'weather throughout the day'). Default: false"
                                )
                            },
                            required=[]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_short_term_weather",
                        description="Provides short-term weather forecast information within 7 hours to 5 days (120 hours). Includes weather prediction information for longer periods.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "location": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Location name where you want to know the weather (e.g., Seoul, Chuncheon, Nowon, Hyoja-dong, etc.). If the user doesn't specify a location or expresses it as 'current location', 'here', 'current', etc., pass an empty string ('')."
                                ),
                                "hours": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="How many hours ahead to check the weather (7-120 hours, default: 24)"
                                ),
                                "full_day": genai.protos.Schema(
                                    type=genai.protos.Type.BOOLEAN,
                                    description="Set to true when user asks for full day weather information (e.g., 'today's weather', 'all day weather', 'weather throughout the day'). Default: false"
                                )
                            },
                            required=[]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_cctv_info",
                        description="Provides CCTV information for specific areas. Offers information and streaming URLs of CCTV cameras that can check real-time road conditions or traffic situations.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "location": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Location name where you want to find CCTV (e.g., Chuncheon, Hyoja-dong, Nowon, Seoul, etc.). Road names or intersection names are also possible."
                                )
                            },
                            required=["location"]
                        )
                    )
                ]
            )
        ] 