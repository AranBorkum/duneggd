#!/usr/bin/env python
'''
Subbuilder of WorldBuilder
'''

# Water Brick website https://practicalpreppers.com/product/10-pack-of-waterbrick-standard-3-5-gallon-tan/
# Water Brich dimensions 9" W x 18" L x 6" H
# Recomended stacking height is 4' so that is 8 height
# Assing the Super structure of these blocks will be 18" by 36" by 48"

import gegede.builder
import math as m
from gegede import Quantity as Q

# for the cavern dimensions, I used the 60% CF for the FD Submission drawings
#http://docs.dunescience.org/cgi-bin/RetrieveFile?docid=11239&filename=EXC%2060PCT%20FD%20Page%20Turn%20Presentation.pdf&version=2

class DetEncLArBuilder(gegede.builder.Builder):
    '''
    Build the Detector Enclosure.
    '''


    #^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^
    def configure(self, 
                  detEncDim          = None, 
                  archRadius         = None,
                  archHalfAngle      = None,
                  ConcreteBeamGap    = None,
                  RadioRockThickness = None,
                  RadioRockMaterial  = None,
                  **kwds):
        
        if detEncDim is None:
            raise ValueError("No value given for detEncDim")
        
        self.detEncMat          = 'Air'
        self.detEncDim          = detEncDim
        self.archRadius         = archRadius    
        self.archHalfAngle      = archHalfAngle
        self.ConcreteBeamGap    = ConcreteBeamGap
        self.RadioRockThickness = RadioRockThickness
        self.RadioRockMaterial  = RadioRockMaterial
        print ("Size of the det enclosure " + str(self.detEncDim))
        # Space from negative face of volDetEnc to closest face of detector
        #  This positions the detector in the enclosure

        self.CryoBldr   = self.get_builder("Cryostat")


    #^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^
    def construct(self, geom):


        # Define the box for the detector enclosure
        encBox = geom.shapes.Box('DetEnclosureBox',
                                 dx=0.5*self.detEncDim[0], 
                                 dy=0.5*self.detEncDim[1],
                                 dz=0.5*self.detEncDim[2])

        # Define the arched roof of the detector enclosure
        encArch = geom.shapes.Tubs('DetEnclosureArch',
                                   rmin = Q('0cm'),
                                   rmax = self.archRadius,
                                   dz   = 0.5*self.detEncDim[2],
                                   sphi = Q('90deg')-self.archHalfAngle,
                                   dphi = self.archHalfAngle*2)

        elevation = self.detEncDim[1]/2 - m.cos(self.archHalfAngle.to('radians')) * self.archRadius
        
        Pos = geom.structure.Position(self.name+'_ArchPos',
                                      Q('0m'), elevation, Q('0m'))

        # Join the arched roof and box together
        encTotal = geom.shapes.Boolean(self.name+"BoolAdd",
                                       type   = 'union',
                                       first  = encBox,
                                       second = encArch,
                                       pos    = Pos)
        
        # detEnc_lv = geom.structure.Volume('volDetEnclosure', material=self.detEncMat, shape=encTotal)
        # self.add_volume(detEnc_lv)


        # Calculate position of detector in the enclosure
        self.CryostatOuterDim = list(self.CryoBldr.CryostatOuterDim)
        self.MainDetCenter = [Q('0m'), 
                              -0.5*self.detEncDim[1] + self.ConcreteBeamGap[1] + 0.5*self.CryostatOuterDim[1] + 0.5*self.RadioRockThickness,
                              -0.5*self.detEncDim[2] + self.ConcreteBeamGap[2] + 0.5*self.CryostatOuterDim[2]]


        # Place some rock
        RockBox   = geom.shapes.Box('RadioRockBox',
                                    dx=0.5*(self.detEncDim[0])+self.RadioRockThickness,
                                    dy=0.5*(self.detEncDim[1])+0.5*self.RadioRockThickness,
                                    dz=0.5*(self.detEncDim[2])+self.RadioRockThickness)        
        

        x         = self.detEncDim[0]+2*self.RadioRockThickness
        r         = self.archRadius+self.RadioRockThickness
        RockAngle = m.degrees(m.asin(x/(2*r)))
        elevation = self.detEncDim[1]/2 - m.cos(m.radians(RockAngle)) * r + 0.5*self.RadioRockThickness
        Tube_pos  = geom.structure.Position('posTube', Q('0m'), elevation, Q('0m'))
        
        RockTup = geom.shapes.Tubs('RockArch',
                                   rmin = Q('0cm'),
                                   rmax = self.archRadius + self.RadioRockThickness,
                                   dz   = 0.5*self.detEncDim[2] + self.RadioRockThickness,
                                   sphi = Q('90deg')-Q(RockAngle, 'deg'),
                                   dphi = 2*Q(RockAngle, 'deg'))

        RockBox = geom.shapes.Boolean('RockAddition',
                                      type   = 'union',
                                      first  = RockBox,
                                      second = RockTup,
                                      pos    = Tube_pos)

        detEnc_lv = geom.structure.Volume('volDetEnclosure', material=self.detEncMat, shape=RockBox)
        self.add_volume(detEnc_lv)        
        
        pos    = geom.structure.Position('posFirstSub', Q('0m'), 0.5*self.RadioRockThickness, Q('0m'))
        RockBox   = geom.shapes.Boolean('FirstSub',
                                        type   = 'subtraction',
                                        first  = RockBox,
                                        second = encTotal,
                                        pos    = pos)

        rock_lv   = geom.structure.Volume('volRadioRockShell', material=self.RadioRockMaterial, shape=RockBox)
        rock_pos  = geom.structure.Position('posRock', Q('0m'), Q('0m'), Q('0m'))
        placeRock = geom.structure.Placement('placeRock', volume=rock_lv, pos=rock_pos)
        
        detEnc_lv.placements.append(placeRock.name)

        
        # Place Cryostat
        posName     = 'Cryo_in_enc'
        cryo_lv     = self.CryoBldr.get_volume('volCryostat')
        cryo_in_enc = geom.structure.Position(posName,
                                              self.MainDetCenter[0],
                                              self.MainDetCenter[1],
                                              self.MainDetCenter[2])
        
        place_cryo_in_E = geom.structure.Placement('place'+posName,
                                                    volume = cryo_lv,
                                                    pos    = cryo_in_enc)
        detEnc_lv.placements.append(place_cryo_in_E.name)
