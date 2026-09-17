
import calendar
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Tính lãi tiền gửi tiết kiệm",
    page_icon="💰",
    layout="wide",
)


# =========================
# HÀM TIỆN ÍCH
# =========================
MONEY_QUANT = Decimal("1")


def D(value) -> Decimal:
    """Chuyển số sang Decimal an toàn."""
    return Decimal(str(value))


def round_money(value: Decimal) -> Decimal:
    """Làm tròn đến 1 đồng."""
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def format_vnd(value: Decimal) -> str:
    """Định dạng tiền VND."""
    amount = int(round_money(value))
    return f"{amount:,.0f}".replace(",", ".") + " ₫"


def parse_vnd_input(value: str) -> Decimal:
    """Chuyển chuỗi tiền có dấu chấm phân tách hàng nghìn thành Decimal."""
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        raise ValueError("Vui lòng nhập số tiền gửi hợp lệ.")
    return Decimal(digits)


# =========================
# Ô NHẬP TIỀN ĐỊNH DẠNG TRỰC TIẾP KHI GÕ
# =========================
MONEY_INPUT_HTML = r"""
<div class="money-input-wrap">
    <label class="money-input-label" for="money-input"></label>
    <input
        id="money-input"
        class="money-input-control"
        type="text"
        inputmode="numeric"
        autocomplete="off"
        spellcheck="false"
    />
    <div class="money-input-help"></div>
</div>
"""

MONEY_INPUT_CSS = r"""
.money-input-wrap {
    width: 100%;
    font-family: var(--font, sans-serif);
}

.money-input-label {
    display: block;
    margin-bottom: 0.35rem;
    font-size: 0.875rem;
    line-height: 1.25rem;
    font-weight: 400;
    color: var(--text-color, inherit);
}

.money-input-control {
    box-sizing: border-box;
    width: 100%;
    min-height: 2.5rem;
    padding: 0.5rem 0.75rem;
    border: 1px solid rgba(49, 51, 63, 0.2);
    border-radius: 0.5rem;
    outline: none;
    background: var(--background-color, transparent);
    color: var(--text-color, inherit);
    font: inherit;
    font-size: 1rem;
    line-height: 1.5rem;
    transition: border-color 0.12s ease, box-shadow 0.12s ease;
}

.money-input-control:focus {
    border-color: rgb(255, 75, 75);
    box-shadow: 0 0 0 1px rgb(255, 75, 75);
}

.money-input-control::placeholder {
    opacity: 0.55;
}

.money-input-help {
    margin-top: 0.25rem;
    min-height: 1rem;
    font-size: 0.75rem;
    line-height: 1rem;
    opacity: 0.7;
}
"""

MONEY_INPUT_JS = r"""
export default function(component) {
    const { setStateValue, parentElement, data } = component;

    const input = parentElement.querySelector('#money-input');
    const label = parentElement.querySelector('.money-input-label');
    const help = parentElement.querySelector('.money-input-help');

    label.textContent = data.label ?? '';
    help.textContent = data.help ?? '';
    input.placeholder = data.placeholder ?? '';

    function onlyDigits(value) {
        let digits = String(value ?? '').replace(/\D/g, '');
        digits = digits.replace(/^0+(?=\d)/, '');
        return digits;
    }

    function formatThousands(value) {
        const digits = onlyDigits(value);
        if (!digits) return '';
        return digits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    }

    function cursorAfterDigitCount(formatted, digitCount) {
        if (digitCount <= 0) return 0;

        let count = 0;
        for (let i = 0; i < formatted.length; i++) {
            if (/\d/.test(formatted[i])) {
                count += 1;
                if (count === digitCount) return i + 1;
            }
        }
        return formatted.length;
    }

    // Chỉ đồng bộ dữ liệu từ Python khi cần. Không ghi đè nội dung
    // đang được người dùng gõ nếu giá trị đã giống nhau.
    const incoming = formatThousands(data.value ?? '');
    if (input.value !== incoming && document.activeElement !== input) {
        input.value = incoming;
    }

    input.oninput = (event) => {
        const raw = event.target.value;
        const oldCursor = event.target.selectionStart ?? raw.length;
        const digitsBeforeCursor = raw
            .slice(0, oldCursor)
            .replace(/\D/g, '')
            .length;

        const formatted = formatThousands(raw);
        event.target.value = formatted;

        const newCursor = cursorAfterDigitCount(
            formatted,
            digitsBeforeCursor
        );
        event.target.setSelectionRange(newCursor, newCursor);

        // Đồng bộ giá trị đã định dạng về Python ngay trong lúc gõ.
        setStateValue('value', formatted);
    };

    input.onkeydown = (event) => {
        // Chỉ cho phép phím điều hướng, chỉnh sửa và tổ hợp phím hệ thống.
        if (
            event.ctrlKey ||
            event.metaKey ||
            event.altKey ||
            ['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight',
             'ArrowUp', 'ArrowDown', 'Home', 'End', 'Tab', 'Enter'].includes(event.key) ||
            /^\d$/.test(event.key)
        ) {
            return;
        }
        event.preventDefault();
    };

    input.onpaste = (event) => {
        event.preventDefault();
        const pasted = (event.clipboardData || window.clipboardData)
            .getData('text');
        const digits = onlyDigits(pasted);
        if (!digits) return;

        const start = input.selectionStart ?? input.value.length;
        const end = input.selectionEnd ?? start;
        const currentDigits = onlyDigits(input.value);
        const digitsBefore = onlyDigits(input.value.slice(0, start));
        const digitsSelected = onlyDigits(input.value.slice(start, end));

        const insertIndex = digitsBefore.length;
        const deleteCount = digitsSelected.length;
        const merged =
            currentDigits.slice(0, insertIndex) +
            digits +
            currentDigits.slice(insertIndex + deleteCount);

        const formatted = formatThousands(merged);
        input.value = formatted;

        const newCursor = cursorAfterDigitCount(
            formatted,
            insertIndex + digits.length
        );
        input.setSelectionRange(newCursor, newCursor);
        setStateValue('value', formatted);
    };
}
"""


def create_money_input_component():
    """Tạo Custom Component v2 cho ô tiền VND."""
    if not hasattr(st.components, "v2"):
        return None

    return st.components.v2.component(
        "formatted_vnd_money_input",
        html=MONEY_INPUT_HTML,
        css=MONEY_INPUT_CSS,
        js=MONEY_INPUT_JS,
    )


MONEY_INPUT_COMPONENT = create_money_input_component()


def vnd_money_input(
    label: str,
    *,
    default: str = "",
    key: str,
    placeholder: str = "",
    help_text: str = "",
) -> str:
    """
    Ô nhập tiền hiển thị dấu chấm hàng nghìn ngay khi người dùng gõ.

    Ví dụ: gõ 500000000 thì ngay trong quá trình nhập sẽ hiển thị
    500.000.000, không cần nhấn Enter và không cần rời khỏi ô nhập.
    """
    if MONEY_INPUT_COMPONENT is None:
        st.error(
            "Tính năng định dạng tiền trực tiếp cần Streamlit 1.51.0 trở lên. "
            "Hãy chạy: pip install -U streamlit"
        )
        st.stop()

    component_state = st.session_state.get(key, {})
    if hasattr(component_state, "get"):
        current_value = component_state.get("value", default)
    else:
        current_value = default

    if not current_value:
        current_value = default

    result = MONEY_INPUT_COMPONENT(
        data={
            "label": label,
            "value": current_value,
            "placeholder": placeholder,
            "help": help_text,
        },
        default={"value": current_value},
        key=key,
        on_value_change=lambda: None,
        width="stretch",
    )

    result_value = getattr(result, "value", None)
    return result_value if result_value is not None else current_value


def format_rate(value: Decimal) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") + "%"


def add_months(d: date, months: int) -> date:
    """Cộng số tháng vào một ngày, tự điều chỉnh ngày cuối tháng."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_term(d: date, term_value: int, term_unit: str) -> date:
    """Tính ngày đáo hạn theo kỳ hạn."""
    if term_unit == "Ngày":
        return d + timedelta(days=term_value)
    if term_unit == "Tháng":
        return add_months(d, term_value)
    if term_unit == "Năm":
        return add_months(d, term_value * 12)
    raise ValueError("Đơn vị kỳ hạn không hợp lệ.")


def interest_by_days(
    principal: Decimal,
    annual_rate_percent: Decimal,
    days: int,
    day_basis: int = 365,
) -> Decimal:
    """
    Tiền lãi = Gốc × Lãi suất năm × Số ngày thực tế / Cơ sở ngày.
    Ngày gửi được tính lãi, ngày kết thúc không được tính lãi.
    Vì vậy số ngày tính lãi = end_date - start_date.
    """
    if days <= 0:
        return Decimal("0")
    return (
        principal
        * annual_rate_percent
        / Decimal("100")
        * Decimal(days)
        / Decimal(day_basis)
    )


def monthly_boundaries(cycle_start: date, cycle_end: date):
    """
    Tạo các mốc trả lãi hàng tháng.
    Mốc cuối cùng luôn là ngày đáo hạn của chu kỳ.
    """
    boundaries = []
    k = 1

    while True:
        candidate = add_months(cycle_start, k)
        if candidate >= cycle_end:
            boundaries.append(cycle_end)
            break
        boundaries.append(candidate)
        k += 1

    return boundaries


def monthly_interest_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    cycle_start: date,
    cycle_end: date,
    day_basis: int,
):
    """Lập lịch trả lãi hàng tháng cho một chu kỳ đầy đủ."""
    rows = []
    prev = cycle_start

    for payment_date in monthly_boundaries(cycle_start, cycle_end):
        days = (payment_date - prev).days
        interest = interest_by_days(
            principal=principal,
            annual_rate_percent=annual_rate,
            days=days,
            day_basis=day_basis,
        )

        rows.append(
            {
                "Ngày nhận lãi": payment_date,
                "Từ ngày": prev,
                "Đến trước ngày": payment_date,
                "Số ngày": days,
                "Lãi suất áp dụng": annual_rate,
                "Tiền lãi": interest,
            }
        )
        prev = payment_date

    return rows


def monthly_paid_before_withdrawal(
    principal: Decimal,
    annual_rate: Decimal,
    cycle_start: date,
    scheduled_cycle_end: date,
    withdrawal_date: date,
    day_basis: int,
):
    """
    Xác định các khoản lãi hàng tháng đã được trả trước ngày rút
    trong một chu kỳ đang bị rút trước hạn.
    """
    rows = []
    prev = cycle_start

    for payment_date in monthly_boundaries(cycle_start, scheduled_cycle_end):
        if payment_date > withdrawal_date:
            break

        days = (payment_date - prev).days
        interest = interest_by_days(
            principal=principal,
            annual_rate_percent=annual_rate,
            days=days,
            day_basis=day_basis,
        )

        rows.append(
            {
                "Ngày nhận lãi": payment_date,
                "Từ ngày": prev,
                "Đến trước ngày": payment_date,
                "Số ngày": days,
                "Lãi suất áp dụng": annual_rate,
                "Tiền lãi": interest,
            }
        )
        prev = payment_date

    return rows


def calculate_deposit(
    principal: Decimal,
    term_rate: Decimal,
    demand_rate: Decimal,
    deposit_date: date,
    withdrawal_date: date,
    term_value: int,
    term_unit: str,
    payout_method: str,
    day_basis: int = 365,
):
    """
    Quy tắc chính:
    1. Mỗi chu kỳ đầy đủ hưởng lãi suất có kỳ hạn.
    2. Nếu khách hàng rút trong một chu kỳ chưa đáo hạn,
       toàn bộ phần thời gian của chu kỳ hiện tại hưởng lãi suất không kỳ hạn.
    3. Các chu kỳ đã đáo hạn trước đó vẫn giữ lãi suất có kỳ hạn.
    4. Nếu chưa rút khi đáo hạn, gốc tự động tái tục với đúng kỳ hạn cũ.
    5. Lãi không nhập gốc. Đây là cơ chế tái tục gốc.
    6. Với nhận lãi trước hoặc nhận lãi hàng tháng,
       nếu rút trước hạn thì phần lãi đã trả trong chu kỳ hiện tại
       được đối trừ khi tất toán để lãi ròng của chu kỳ đó
       đúng bằng lãi suất không kỳ hạn.
    """
    if withdrawal_date <= deposit_date:
        raise ValueError("Ngày rút tiền phải sau ngày gửi tiền.")

    if principal <= 0:
        raise ValueError("Số tiền gửi phải lớn hơn 0.")

    if term_rate < 0 or demand_rate < 0:
        raise ValueError("Lãi suất không được âm.")

    if term_value <= 0:
        raise ValueError("Kỳ hạn phải lớn hơn 0.")

    schedule = []
    cycle_no = 1
    cycle_start = deposit_date

    interest_paid_before_settlement = Decimal("0")
    settlement_interest_or_adjustment = Decimal("0")
    term_interest_total = Decimal("0")
    demand_interest_total = Decimal("0")
    completed_cycles = 0
    is_early_withdrawal = False

    while True:
        scheduled_end = add_term(cycle_start, term_value, term_unit)

        # Trường hợp ngày rút đúng hoặc sau ngày đáo hạn của chu kỳ hiện tại
        if withdrawal_date >= scheduled_end:
            completed_cycles += 1
            days = (scheduled_end - cycle_start).days
            full_cycle_interest = interest_by_days(
                principal,
                term_rate,
                days,
                day_basis,
            )
            term_interest_total += full_cycle_interest

            if payout_method == "Nhận lãi trước":
                payment_date = cycle_start
                schedule.append(
                    {
                        "Chu kỳ": cycle_no,
                        "Loại giao dịch": "Trả lãi trước",
                        "Ngày thanh toán": payment_date,
                        "Từ ngày": cycle_start,
                        "Đến trước ngày": scheduled_end,
                        "Số ngày": days,
                        "Lãi suất": format_rate(term_rate),
                        "Số tiền": round_money(full_cycle_interest),
                    }
                )
                interest_paid_before_settlement += full_cycle_interest

            elif payout_method == "Nhận lãi hàng tháng":
                monthly_rows = monthly_interest_schedule(
                    principal,
                    term_rate,
                    cycle_start,
                    scheduled_end,
                    day_basis,
                )
                for row in monthly_rows:
                    schedule.append(
                        {
                            "Chu kỳ": cycle_no,
                            "Loại giao dịch": "Trả lãi hàng tháng",
                            "Ngày thanh toán": row["Ngày nhận lãi"],
                            "Từ ngày": row["Từ ngày"],
                            "Đến trước ngày": row["Đến trước ngày"],
                            "Số ngày": row["Số ngày"],
                            "Lãi suất": format_rate(term_rate),
                            "Số tiền": round_money(row["Tiền lãi"]),
                        }
                    )
                    interest_paid_before_settlement += row["Tiền lãi"]

            elif payout_method == "Nhận lãi cuối kỳ":
                schedule.append(
                    {
                        "Chu kỳ": cycle_no,
                        "Loại giao dịch": "Trả lãi cuối kỳ",
                        "Ngày thanh toán": scheduled_end,
                        "Từ ngày": cycle_start,
                        "Đến trước ngày": scheduled_end,
                        "Số ngày": days,
                        "Lãi suất": format_rate(term_rate),
                        "Số tiền": round_money(full_cycle_interest),
                    }
                )
                interest_paid_before_settlement += full_cycle_interest

            # Nếu rút đúng ngày đáo hạn, kết thúc tại đây
            if withdrawal_date == scheduled_end:
                schedule.append(
                    {
                        "Chu kỳ": cycle_no,
                        "Loại giao dịch": "Hoàn trả tiền gốc",
                        "Ngày thanh toán": withdrawal_date,
                        "Từ ngày": "",
                        "Đến trước ngày": "",
                        "Số ngày": "",
                        "Lãi suất": "",
                        "Số tiền": round_money(principal),
                    }
                )
                break

            # Không rút tại đáo hạn: tự động tái tục gốc cùng kỳ hạn
            cycle_start = scheduled_end
            cycle_no += 1
            continue

        # Trường hợp rút trước ngày đáo hạn của chu kỳ hiện tại
        is_early_withdrawal = True
        actual_days = (withdrawal_date - cycle_start).days
        demand_interest = interest_by_days(
            principal,
            demand_rate,
            actual_days,
            day_basis,
        )
        demand_interest_total += demand_interest

        already_paid_current_cycle = Decimal("0")

        if payout_method == "Nhận lãi trước":
            scheduled_days = (scheduled_end - cycle_start).days
            upfront_interest = interest_by_days(
                principal,
                term_rate,
                scheduled_days,
                day_basis,
            )
            already_paid_current_cycle = upfront_interest
            interest_paid_before_settlement += upfront_interest

            schedule.append(
                {
                    "Chu kỳ": cycle_no,
                    "Loại giao dịch": "Lãi trước đã nhận",
                    "Ngày thanh toán": cycle_start,
                    "Từ ngày": cycle_start,
                    "Đến trước ngày": scheduled_end,
                    "Số ngày": scheduled_days,
                    "Lãi suất": format_rate(term_rate),
                    "Số tiền": round_money(upfront_interest),
                }
            )

        elif payout_method == "Nhận lãi hàng tháng":
            paid_rows = monthly_paid_before_withdrawal(
                principal,
                term_rate,
                cycle_start,
                scheduled_end,
                withdrawal_date,
                day_basis,
            )

            for row in paid_rows:
                already_paid_current_cycle += row["Tiền lãi"]
                interest_paid_before_settlement += row["Tiền lãi"]

                schedule.append(
                    {
                        "Chu kỳ": cycle_no,
                        "Loại giao dịch": "Lãi tháng đã nhận",
                        "Ngày thanh toán": row["Ngày nhận lãi"],
                        "Từ ngày": row["Từ ngày"],
                        "Đến trước ngày": row["Đến trước ngày"],
                        "Số ngày": row["Số ngày"],
                        "Lãi suất": format_rate(term_rate),
                        "Số tiền": round_money(row["Tiền lãi"]),
                    }
                )

        # Số điều chỉnh tại ngày rút:
        # Lãi đúng được hưởng theo không kỳ hạn trừ đi phần đã trả trong chu kỳ hiện tại.
        adjustment = demand_interest - already_paid_current_cycle
        settlement_interest_or_adjustment = adjustment

        schedule.append(
            {
                "Chu kỳ": cycle_no,
                "Loại giao dịch": (
                    "Lãi không kỳ hạn khi rút trước hạn"
                    if already_paid_current_cycle == 0
                    else "Điều chỉnh lãi khi rút trước hạn"
                ),
                "Ngày thanh toán": withdrawal_date,
                "Từ ngày": cycle_start,
                "Đến trước ngày": withdrawal_date,
                "Số ngày": actual_days,
                "Lãi suất": format_rate(demand_rate),
                "Số tiền": round_money(adjustment),
            }
        )

        schedule.append(
            {
                "Chu kỳ": cycle_no,
                "Loại giao dịch": "Hoàn trả tiền gốc",
                "Ngày thanh toán": withdrawal_date,
                "Từ ngày": "",
                "Đến trước ngày": "",
                "Số ngày": "",
                "Lãi suất": "",
                "Số tiền": round_money(principal),
            }
        )
        break

    net_interest = term_interest_total + demand_interest_total
    total_received = principal + net_interest
    settlement_amount = principal + settlement_interest_or_adjustment

    return {
        "completed_cycles": completed_cycles,
        "is_early_withdrawal": is_early_withdrawal,
        "term_interest_total": term_interest_total,
        "demand_interest_total": demand_interest_total,
        "net_interest": net_interest,
        "interest_paid_before_settlement": interest_paid_before_settlement,
        "settlement_interest_or_adjustment": settlement_interest_or_adjustment,
        "settlement_amount": settlement_amount,
        "total_received": total_received,
        "schedule": schedule,
    }


# =========================
# GIAO DIỆN
# =========================
st.title("💰 Ứng dụng tính lãi tiền gửi tiết kiệm_Thịnh Đẹp Try")

st.caption(
    "Ứng dụng tính theo số ngày thực tế. Ngày gửi được tính lãi, "
    "ngày đáo hạn hoặc ngày rút không được tính lãi."
)

col1, col2 = st.columns(2)

with col1:
    principal_input = vnd_money_input(
        "Số tiền khách hàng gửi (VND)",
        default="100.000.000",
        key="principal_money_input",
        placeholder="Ví dụ: 500000000",
        help_text=(
            "Dấu chấm phân cách hàng nghìn được thêm ngay khi gõ. "
            "Ví dụ: 500000000 → 500.000.000."
        ),
    )

    term_rate_input = st.number_input(
        "Lãi suất có kỳ hạn (%/năm)",
        min_value=0.0,
        value=5.0,
        step=0.1,
        format="%.3f",
    )

    demand_rate_input = st.number_input(
        "Lãi suất không kỳ hạn (%/năm)",
        min_value=0.0,
        value=0.2,
        step=0.05,
        format="%.3f",
    )

    payout_method = st.radio(
        "Cách nhận tiền lãi",
        [
            "Nhận lãi trước",
            "Nhận lãi hàng tháng",
            "Nhận lãi cuối kỳ",
        ],
    )

with col2:
    deposit_date_input = st.date_input(
        "Ngày gửi tiền",
        value=date.today(),
        format="DD/MM/YYYY",
    )

    withdrawal_date_input = st.date_input(
        "Ngày rút tiền",
        value=date.today() + timedelta(days=365),
        format="DD/MM/YYYY",
    )

    term_col1, term_col2 = st.columns([2, 1])

    with term_col1:
        term_value_input = st.number_input(
            "Kỳ hạn gửi tiền",
            min_value=1,
            value=12,
            step=1,
        )

    with term_col2:
        term_unit_input = st.selectbox(
            "Đơn vị",
            ["Tháng", "Ngày", "Năm"],
        )

    day_basis = st.selectbox(
        "Cơ sở tính lãi",
        [365, 360],
        index=0,
        help=(
            "Mặc định 365 ngày/năm. "
            "Có thể đổi thành 360 nếu quy định của ngân hàng yêu cầu."
        ),
    )

calculate_button = st.button(
    "TÍNH TOÁN",
    type="primary",
    use_container_width=True,
)


# =========================
# KẾT QUẢ
# =========================
if calculate_button:
    try:
        principal = parse_vnd_input(principal_input)
        term_rate = D(term_rate_input)
        demand_rate = D(demand_rate_input)

        result = calculate_deposit(
            principal=principal,
            term_rate=term_rate,
            demand_rate=demand_rate,
            deposit_date=deposit_date_input,
            withdrawal_date=withdrawal_date_input,
            term_value=int(term_value_input),
            term_unit=term_unit_input,
            payout_method=payout_method,
            day_basis=int(day_basis),
        )

        first_maturity = add_term(
            deposit_date_input,
            int(term_value_input),
            term_unit_input,
        )

        st.divider()
        st.subheader("Kết quả tính toán")

        c1, c2, c3 = st.columns(3)
        c1.metric("Tiền gốc", format_vnd(principal))
        c2.metric("Tổng tiền lãi ròng", format_vnd(result["net_interest"]))
        c3.metric(
            "Tổng gốc và lãi khách hàng nhận",
            format_vnd(result["total_received"]),
        )

        c4, c5, c6 = st.columns(3)
        c4.metric("Ngày đáo hạn đầu tiên", first_maturity.strftime("%d/%m/%Y"))
        c5.metric("Số kỳ đã hoàn tất", str(result["completed_cycles"]))
        c6.metric(
            "Trạng thái kỳ hiện tại",
            "Rút trước hạn" if result["is_early_withdrawal"] else "Đúng ngày đáo hạn",
        )

        if result["is_early_withdrawal"]:
            st.warning(
                "Khách hàng rút trong một kỳ chưa đáo hạn. "
                "Phần thời gian của kỳ hiện tại được tính lại theo lãi suất không kỳ hạn. "
                "Các kỳ đã đáo hạn trước đó vẫn giữ lãi suất có kỳ hạn."
            )

            st.write(
                f"Tiền lãi không kỳ hạn của kỳ đang rút trước hạn: "
                f"**{format_vnd(result['demand_interest_total'])}**"
            )

            if result["settlement_interest_or_adjustment"] < 0:
                st.write(
                    "Do khách hàng đã nhận lãi trước hoặc lãi hàng tháng cao hơn "
                    "mức lãi không kỳ hạn được hưởng trong kỳ hiện tại, "
                    f"ngân hàng cần đối trừ **{format_vnd(abs(result['settlement_interest_or_adjustment']))}** "
                    "khi tất toán."
                )

            st.write(
                f"Số tiền thực nhận tại đúng ngày rút, sau khi tính phần đã nhận trước đó: "
                f"**{format_vnd(result['settlement_amount'])}**"
            )

        st.info(
            "Quy tắc tái tục đang áp dụng: tái tục tiền gốc, giữ nguyên kỳ hạn và "
            "lãi suất có kỳ hạn đã nhập. Tiền lãi được chi trả theo phương thức khách hàng chọn."
        )

        st.subheader("Chi tiết lịch trả lãi và tất toán")

        df = pd.DataFrame(result["schedule"])

        if not df.empty:
            display_df = df.copy()

            for col in ["Ngày thanh toán", "Từ ngày", "Đến trước ngày"]:
                display_df[col] = display_df[col].apply(
                    lambda x: x.strftime("%d/%m/%Y")
                    if isinstance(x, date)
                    else x
                )

            display_df["Số tiền"] = display_df["Số tiền"].apply(format_vnd)

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Quy tắc tính đang được áp dụng"):
            st.markdown(
                """
1. Ngày gửi tiền được tính lãi. Ngày đáo hạn hoặc ngày rút tiền không được tính lãi.

2. Số ngày tính lãi của một khoảng thời gian bằng ngày kết thúc trừ ngày bắt đầu.

3. Tiền lãi được tính theo công thức: tiền gốc nhân lãi suất năm nhân số ngày thực tế chia cho cơ sở ngày.

4. Nếu khách hàng rút trước hạn trong kỳ hiện tại, toàn bộ số ngày của kỳ hiện tại chỉ hưởng lãi suất không kỳ hạn.

5. Nếu khách hàng đã đi qua một hoặc nhiều kỳ đáo hạn, các kỳ đã hoàn tất vẫn hưởng lãi suất có kỳ hạn. Kỳ đang dở tại ngày rút được tính theo lãi suất không kỳ hạn.

6. Nếu khách hàng không rút khi đến hạn, tiền gốc tự động được tái tục với đúng kỳ hạn ban đầu.

7. Với phương thức nhận lãi trước hoặc nhận lãi hàng tháng, nếu khách hàng rút trước hạn thì ứng dụng đối trừ phần lãi đã nhận trong kỳ hiện tại để lãi ròng của kỳ đó đúng bằng lãi suất không kỳ hạn.

8. Ứng dụng hiện giả định tái tục gốc. Lãi không nhập vào gốc ở kỳ kế tiếp.
                """
            )

    except Exception as exc:
        st.error(str(exc))
