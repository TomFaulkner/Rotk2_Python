from Data import Data

# Import for name translation
try:
    from Battle.officer_names import get_officer_name
    import translations
except ImportError:
    get_officer_name = None
    translations = None


class Officer(object):
    # region properties
    Offset = 0
    RulerNo = 0
    Name = ""
    Int = 0
    War = 0
    Chm = 0
    Soldiers = 0
    Weapons = 0
    TrainingLevel = 0
    Age = 0
    Loyalty = 0
    shiwei = 0
    IsSick = False
    SickMonth = 0
    yili = 0
    rende = 0
    yewang = 0
    SpyBlongedToRuler = 0
    SpyInCityNo = 0
    Compatibility = 0
    WillDieInNextYear = 0
    CanMoveNow = 0
    MonthCannotMove = 0
    xueyuan = 0
    NextOfficerOffset = 0
    Portrait = 0
    IsUnClaimed = False
    IsFree = False
    Arms = 100
    # endregion properties

    def GetName(self):
        # Check if we should use English names
        if translations and get_officer_name:
            try:
                # Get current language from translation manager
                lang = translations.get_translation_manager()._language
                if lang == "en":
                    # Calculate officer ID from offset
                    officer_id = (self.Offset - Data.OFFICER_START) // Data.OFFICER_SIZE
                    return get_officer_name(officer_id)
            except Exception:
                pass  # Fall back to Chinese name on any error

        # Return Chinese name (original implementation)
        officer_name_data = ""
        index = 0
        while True:
            if index > 12:
                break
            if Data.BUF[self.Offset + 0x1C + index] == 0:
                break

            if Data.BUF[self.Offset + 0x1C + index + 0] < 0x80:
                officer_name_data += chr(Data.BUF[self.Offset + 0x1C + index + 0])
                index += 1
                continue

            s = (
                Data.BUF[self.Offset + 0x1C + index + 0] * 256
                + Data.BUF[self.Offset + 0x1C + index + 1]
            )

            if s not in [0xD8F0, 0xD8F1, 0xD8F2, 0xD8F3, 0xD8F4, 0xD8F5]:
                officer_name_data += "$" + str(Data.CNINDEX[s]) + "$"
            else:
                officer_name_data += "$" + str(s) + "$"
            index += 2

        return officer_name_data

    @staticmethod
    def FromBuffer(buffer, gen_no, year):
        o = Officer()
        o.Offset = Data.OFFICER_START + Data.OFFICER_SIZE * gen_no
        o.NextOfficerOffset = Data.GetWordFromOffset(buffer, 0x00)

        o.Name = o.GetName()
        o.Int = buffer[0x04]
        o.War = buffer[0x05]
        o.Chm = buffer[0x06]
        o.yili = buffer[0x07]
        o.rende = buffer[0x08]
        o.yewang = buffer[0x09]
        o.RulerNo = buffer[0x0A]
        o.Loyalty = buffer[0x0B]
        o.shiwei = buffer[0x0C]
        o.SpyBlongedToRuler = buffer[0x0D]
        o.SpyInCityNo = buffer[0x0E]
        o.Compatibility = buffer[0x0F]

        o.xueyuan = Data.GetWordFromOffset(buffer, 0x10)
        o.Soldiers = Data.GetWordFromOffset(buffer, 0x12)
        o.Weapons = Data.GetWordFromOffset(buffer, 0x14)
        if o.Soldiers == 0:
            o.Arms = 100
        else:
            o.Arms = min(int((100 * o.Weapons) / o.Soldiers), 100)
        o.TrainingLevel = buffer[0x16]
        o.Age = year - buffer[0x19] + 1

        o.IsSick = (buffer[0x03] & 0x0F) > 0
        o.SickMonth = buffer[0x03] & 0x0F

        o.WillDieInNextYear = buffer[0x02] >> 4
        o.CanMoveNow = (buffer[0x02] & 0x0F) != 1
        o.MonthCannotMove = buffer[0x03] >> 4
        o.Portrait = (buffer[0x1B] << 8) + buffer[0x1A] - 1

        return o

    @staticmethod
    def FromOffset(offset):
        if offset == 0:
            return None

        if (offset - Data.OFFICER_START) % Data.OFFICER_SIZE > 0:
            raise Exception("Invalid officer offset.")

        seq = int((offset - Data.OFFICER_START) / Data.OFFICER_SIZE)

        return Officer.FromBuffer(
            Data.BUF[offset : offset + Data.OFFICER_SIZE],
            seq,
            Data.BUF[0x45] * 256 + Data.BUF[0x44],
        )

    def IsGovernor(self):
        for i in range(0, 41):
            governor_offset = Data.GetWordFromOffset(
                Data.BUF, Data.PROVINCE_START + Data.PROVINCE_SIZE * i + 2
            )
            if self.Offset == governor_offset:
                return True
        return False

    def IsAdvisor(self):
        for i in range(0, 16):
            advisor_offset = Data.GetWordFromOffset(
                Data.BUF, Data.RULER_START + Data.RULER_SIZE * i + 4
            )
            if self.Offset == advisor_offset:
                return True

        return False

    def IsRuler(self):
        for i in range(0, 16):
            ruler_offset = Data.GetWordFromOffset(
                Data.BUF, Data.RULER_START + Data.RULER_SIZE * i + 0
            )
            if self.Offset == ruler_offset:
                return True
        return False

    def Flush(self):
        Data.BUF[self.Offset + 0x00] = self.NextOfficerOffset % 256
        Data.BUF[self.Offset + 0x01] = self.NextOfficerOffset >> 8

        Data.BUF[self.Offset + 0x04] = self.Int
        Data.BUF[self.Offset + 0x05] = self.War
        Data.BUF[self.Offset + 0x06] = self.Chm
        Data.BUF[self.Offset + 0x07] = self.yili
        Data.BUF[self.Offset + 0x08] = self.rende
        Data.BUF[self.Offset + 0x09] = self.yewang
        Data.BUF[self.Offset + 0x0A] = self.RulerNo
        Data.BUF[self.Offset + 0x0B] = self.Loyalty
        Data.BUF[self.Offset + 0x12] = self.Soldiers % 256
        Data.BUF[self.Offset + 0x13] = self.Soldiers >> 8
        Data.BUF[self.Offset + 0x14] = self.Weapons % 256
        Data.BUF[self.Offset + 0x15] = self.Weapons >> 8
        Data.BUF[self.Offset + 0x16] = self.TrainingLevel

        Data.BUF[self.Offset + 0x0C] = self.shiwei
        Data.BUF[self.Offset + 0x0D] = self.SpyBlongedToRuler

        Data.BUF[self.Offset + 0x0E] = self.SpyInCityNo
        Data.BUF[self.Offset + 0x0F] = self.Compatibility

    def SetActionStatus(self):
        status = Data.BUF[self.Offset + 2]
        Data.BUF[self.Offset + 2] = status | 1

    def CanAction(self):
        return (Data.BUF[self.Offset + 2] & 1) != 1
        # 生病暂时不知道是否需要判断
        # or ((Data.BUF[officer.Offset+3] & 1) != 1)

    @property
    def tiger_wolf_susceptibility(self) -> int:
        """
        Calculate Tiger-Wolf (虎狼之計) susceptibility.

        Higher value = easier to convince to rebel.
        Formula: ambition - honor (yewang - yili)
        Range: roughly -100 to +100

        Examples:
        - Li Jue type: High ambition, low honor = high susceptibility
        - Loyal officer: Low ambition, high honor = negative (resistant)

        Returns:
            Susceptibility score (higher = easier to flip)
        """
        return self.yewang - self.yili

    def can_be_tiger_wolfed(self, current_loyalty: int = None, bribe_amount: int = 0) -> bool:
        """
        Check if this officer can be flipped with Tiger-Wolf tactics.

        Args:
            current_loyalty: Officer's current loyalty (uses self.Loyalty if None)
            bribe_amount: Amount of gold offered as bribe

        Returns:
            True if tiger-wolf trick succeeds
        """
        import random

        loyalty = current_loyalty if current_loyalty is not None else self.Loyalty
        susceptibility = self.tiger_wolf_susceptibility

        # Base chance calculation
        base_chance = (100 - loyalty) + (susceptibility * 1.5) + (bribe_amount // 800)

        # Clamp chance between 5% and 95%
        success_chance = max(5, min(95, base_chance))

        return random.random() < (success_chance / 100.0)

    @staticmethod
    def GetAdvisor():
        current_ruler_offset = Data.GetWordFromOffset(Data.BUF, Data.CURRENT_RULER_OFFSET)
        advisor_offset = Data.GetWordFromOffset(Data.BUF, current_ruler_offset + 4)
        return Officer.FromOffset(advisor_offset)

    def SetAdvisor(self):
        current_ruler_offset = (
            Data.BUF[Data.CURRENT_RULER_OFFSET + 1] * 256 + Data.BUF[Data.CURRENT_RULER_OFFSET]
        )
        Data.BUF[current_ruler_offset + 5] = self.Offset >> 8
        Data.BUF[current_ruler_offset + 4] = self.Offset % 256
