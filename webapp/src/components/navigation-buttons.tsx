import React from "react";

type NavButton = {
  label: string;
  onClick: () => void;
};

type NavigationButtonsProps = {
  buttons: NavButton[];
};

export function NavigationButtons({ buttons }: NavigationButtonsProps) {
  return (
    <div className="grid grid-cols-4 gap-2 mb-4">
      {buttons.map((button, index) => (
        <button
          key={index}
          className="border border-gray-400 p-4 flex items-center justify-center rounded"
          onClick={button.onClick}
        >
          {button.label}
        </button>
      ))}
    </div>
  );
}
