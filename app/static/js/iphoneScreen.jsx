import React from "react";
import image1 from "./image-1.png";

export const IphonePro = () => {
  return (
    <div className="bg-[#121212a6] flex flex-row justify-center w-full">
      <div className="bg-[#121212a6] w-[402px] h-[874px] relative">
        <img
          className="absolute w-[252px] h-[126px] top-[91px] left-[75px] mix-blend-multiply object-cover"
          alt="Image"
          src={image1}
        />

        <div className="w-[175px] top-[259px] left-[114px] [font-family:'Island_Moments-Regular',Helvetica] whitespace-nowrap absolute font-normal text-white text-2xl tracking-[0] leading-[normal]">
          Вход в систему
        </div>

        <div className="absolute w-[193px] h-[66px] top-[322px] left-[106px]">
          <div className="relative w-[191px] h-[66px] bg-[#9f9f9f]">
            <div className="absolute w-[170px] top-1 left-4 [font-family:'Instrument_Sans-Regular',Helvetica] font-normal text-white text-2xl tracking-[0] leading-[normal]">
              Email/Телефон
            </div>
          </div>
        </div>

        <div className="absolute w-[193px] h-[66px] top-[430px] left-[106px]">
          <div className="relative w-[191px] h-[66px] bg-[#9f9f9f]">
            <div className="w-[170px] top-[7px] left-4 [font-family:'Instrument_Sans-Regular',Helvetica] absolute font-normal text-white text-2xl tracking-[0] leading-[normal]">
              Пароль
            </div>
          </div>
        </div>

        <div className="absolute w-[264px] h-[137px] top-[660px] left-20">
          <div className="absolute w-[244px] h-[105px] top-0 left-0">
            <div className="relative w-[242px] h-[105px]">
              <div className="absolute w-[242px] h-[92px] top-0 left-0 bg-[#121212a6]" />

              <div className="w-[87px] top-[34px] left-[85px] [font-family:'Instrument_Sans-Regular',Helvetica] absolute font-normal text-white text-2xl tracking-[0] leading-[normal]">
                Войти
              </div>
            </div>
          </div>

          <div className="w-[241px] h-[33px] top-[104px] left-[23px] [font-family:'Instrument_Sans-Regular',Helvetica] absolute font-normal text-white text-2xl tracking-[0] leading-[normal]">
            Забыли пароль?
          </div>
        </div>
      </div>
    </div>
  );
};
